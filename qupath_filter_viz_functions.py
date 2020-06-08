def coordFilter(df):
    '''set x,y slice coordinates to filter cells'''
    
    df = df.reset_index().drop(columns='index')

    x_min,x_max = (float(x) for x in input('x limits:').split())
    y_min,y_max = (float(x) for x in input('y limits:').split())
    
    def incSpace(x,y):
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return 'Y'
        else:
            return 'N'
        
    df['coord_bool'] = df[['centroid_x','centroid_y']].apply(lambda x:incSpace(*x),axis=1)
    
    return df

def channelFilter(df):
    '''set channel parameters to filter cells'''
    
    df = df.reset_index().drop(columns='index')
    
    z = input('Enter "and" for conjunction or "or" for disjunction of parameters:')
    a, b = (float(x) for x in input('red filter:').split())
    c, d = (float(x) for x in input('green filter:').split())
    e, f = (float(x) for x in input('blue filter:').split())
    
    def filterAND(red,green,blue):
        if a <= red <= b and c <= green <= d and e <= blue <= f:
            return 'Y'
        else:
            return 'N'
    
    def filterOR(red,green,blue):
        if a <= red <= b or c <= green <= d or e <= blue <= f:
            return 'Y'
        else:
            return 'N'
    
    if z == 'and': 
        df['channel_bool'] = df[['ratio_red','ratio_green','ratio_blue']].apply(lambda x:filterAND(*x),axis=1) 
    elif z == 'or':
        df['channel_bool'] = df[['ratio_red','ratio_green','ratio_blue']].apply(lambda x:filterOR(*x),axis=1)
    
    return df

def clusterFilter(df,clusters):
    '''input df and list of clusters to filter'''
    
    if type(clusters) != list:
        print('Error: cluster input must be list type')
        return None
    
    df = df.reset_index().drop(columns='index')
    
    def incCluster(x):
        if x in clusters:
            return 'Y'
        else:
            return 'N'
    
    df['cluster_bool'] = df['c_label'].apply(lambda x:incCluster(x))
    
    return df

def stackedBar(df,filtered,column_filter):
    
    import pandas as pd
    from bokeh.plotting import figure,show
    from bokeh.io import output_notebook,output_file
    from bokeh.models import SingleIntervalTicker, LinearAxis
    output_notebook()
    
    '''return stacked bar viz with filter parameters returned as highlighted
    three arguments: dataframe, filtered = True/False to call highlight, and column with bool value'''
    
    if filtered is not True and filtered is not False:
        return 'Error: filter not declared'
    
    if type(df) != pd.core.frame.DataFrame:
        return 'Error: input must be dataframe'
    
    df = df.reset_index().drop(columns='index')
    def roundup(x):
            return x if x % 100 == 0 else x + 100 - x % 100
    
    X_range = list(df.index)
    X_range = list(map(str, X_range))
    channels = ['red', 'green', 'blue']
    
    if filtered is False:
        colour = ['#FF0000','#00FF00','#0000FF']    
    
        data = {'X' : X_range,
                'red' : df['ratio_red'],
                'green' : df['ratio_green'],
                'blue' : df['ratio_blue']}
        
        p = figure(x_range=X_range, 
                   plot_height=400,
                   plot_width = (df.shape[0]+300) *2,
                   title='cell channel ratios',
                   tools="hover",
                   tooltips="$name @$name")
        
        p.vbar_stack(channels, x='X', width=0.7, color=colour, source=data,line_color='black', line_width=0.1)
        
        p.y_range.start = 0
        p.y_range.end = 1
        p.x_range.range_padding = 0
        p.xaxis.visible = False
        
        ticker = SingleIntervalTicker(interval=roundup(df.shape[0]/12))
        xaxis = LinearAxis(ticker=ticker)
        p.add_layout(xaxis, 'below')
        return show(p)
    
    if filtered == True:
        if column_filter not in df.columns:
            return 'column_filter not found'
        
        df_filter = df[df[column_filter] == 'Y']
        df_background = df[df[column_filter] == 'N']
        
        #generate data for filtered/highlighted bars
        X_filter = list(df_filter.index)
        X_filter = list(map(str, X_filter))

        colour_filter = ['#FF0000','#00FF00','#0000FF']

        data_filter = {'X_filter' : X_filter,
                        'red' : df_filter['ratio_red'],
                        'green' : df_filter['ratio_green'],
                        'blue' : df_filter['ratio_blue']}

        #generate data for background bars
        X_background = list(df_background.index)
        X_background = list(map(str, X_background))

        colour_background = ['#590000','#004600','#000050']

        data_background = {'X_background' : X_background,
                        'red' : df_background['ratio_red'],
                        'green' : df_background['ratio_green'],
                        'blue' : df_background['ratio_blue']}

        #construct figure and call vbar_stack for filtered and background data
        #use dataframe.index both for initial X_range and then for df_filter and df_background
        p = figure(x_range=X_range, 
                   plot_height=400,
                   plot_width = (df.shape[0]+300) *2,
                   title='cell channel ratios',
                   tools="hover",
                   tooltips="$name @$name")

        p.vbar_stack(channels, x='X_filter', width=0.7, color=colour_filter, source=data_filter,line_color='black', line_width=0.1)
        p.vbar_stack(channels, x='X_background', width=0.7, color=colour_background, source=data_background,line_color='black', line_width=0.1)

        p.y_range.start = 0
        p.y_range.end = 1
        p.x_range.range_padding = 0
        p.xaxis.visible = False
    
        ticker = SingleIntervalTicker(interval=roundup(df.shape[0]/12))
        xaxis = LinearAxis(ticker=ticker)
        p.add_layout(xaxis, 'below')
        return show(p)      

def imageMask(image,df):
    
    import matplotlib.pyplot as plt
    
    '''input original image and dataframe
    return masked image of dataframe cells'''

    import numpy as np
    
    def tupleCoords(x,y):
                return (int(x),int(y))

    coords = df[['centroid_x','centroid_y']].apply(lambda x:tupleCoords(*x),axis=1)
    
    min_coord = 0
    max_x_coord = image[:,:,0].shape[0]
    max_y_coord = image[:,:,0].shape[1]
    
    border_dimension = 30
    border_width = 5

    def borderLimits(coord,max_coord):
        '''return matrix slice values for square boundary for centroid coordinates'''
        if coord - border_dimension < min_coord:
            lower_lim = min_coord
        else:
            lower_lim = coord - border_dimension
            
        if coord + border_dimension > max_coord:
            upper_lim = max_coord
        else:
            upper_lim = coord + border_dimension
            
        return lower_lim, upper_lim

    def borderPad(x_lower_lim,x_upper_lim,y_lower_lim,y_upper_lim):
        '''pad slice values with white border in RGB channels'''
        inner_slice = image[x_lower_lim + border_width:x_upper_lim - border_width,y_lower_lim + border_width:y_upper_lim - border_width,:]
    
        r_pad = np.pad(inner_slice[:,:,0], pad_width=border_width, mode='constant', constant_values=255)
        g_pad = np.pad(inner_slice[:,:,1], pad_width=border_width, mode='constant', constant_values=255)
        b_pad = np.pad(inner_slice[:,:,2], pad_width=border_width, mode='constant', constant_values=255)
    
        rgb_border = np.dstack((r_pad,g_pad,b_pad))
            
        return rgb_border
    
    def singleMask(image,x,y):
        '''set mask matrix to original image matrix'''
        x_lower_lim,x_upper_lim = borderLimits(x,max_x_coord)
        y_lower_lim,y_upper_lim = borderLimits(y,max_y_coord)
        
        image[x_lower_lim:x_upper_lim,y_lower_lim:y_upper_lim] = borderPad(x_lower_lim,x_upper_lim,y_lower_lim,y_upper_lim)
        
        return image
    
    for i in coords:
        new_image = singleMask(image,i[0],i[1])
    
    plt.figure(figsize=(12,12))
    
    return plt.imshow(new_image)

def emptyMatrixViz(df):
    '''input list of tuple coordinates 
       return viz of empty matrix and coordinate cells as RGB square proportional to cell channel values'''
    
    import matplotlib.pyplot as plt
    import numpy as np
    from tqdm import tqdm
    
    def centroidMinMax(coord):
        '''return slice values which will correspond to a single cell in numpy image matrix
           can change size of slice (cell size) according to number of cells and image size'''
    
        #set min/max according to image size
        min_coord = 0
        max_coord = 2844
    
        #set minimum dimension for cell size in image
        #minimum where centroid coordinate is min or max i.e. on edge of image
        #else cell dimension will be twice minimum dimension
        minium_dimension = 5
    
        #check centroid coordinate is not on edge of image
        #if so, return min/max coordinate
        #else return slice as centroid coordinate +- minium_dimension
        if coord - minium_dimension < min_coord:
            coord_low_lim = min_coord
        else:
            coord_low_lim = coord - minium_dimension
        
        if coord + minium_dimension > max_coord:
            coord_upper_lim = max_coord
        else:
            coord_upper_lim = coord + minium_dimension
    
        return (int(coord_low_lim),int(coord_upper_lim))
    
    image = np.zeros((2845,2845,3), 'uint16')
    
    for i in tqdm(df.index):
        x_limits,y_limits = centroidMinMax(df.loc[i].get('centroid_x')),centroidMinMax(df.loc[i].get('centroid_y'))
    
        image[:,:,0][x_limits[0]:x_limits[1],y_limits[0]:y_limits[1]] = df.loc[i].get('rgb_red')
        image[:,:,1][x_limits[0]:x_limits[1],y_limits[0]:y_limits[1]] = df.loc[i].get('rgb_green')
        image[:,:,2][x_limits[0]:x_limits[1],y_limits[0]:y_limits[1]] = df.loc[i].get('rgb_blue')
    
    plt.figure(figsize=(12,12))
    
    return plt.imshow(image)
