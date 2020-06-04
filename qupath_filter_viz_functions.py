def coordFilter(df):
    '''set x,y slice coordinates to filter cells'''

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

def clusterFilter(df):
    '''choose 1+ clusters by which to filter cells'''
    
    clusters = input('filter clusters:').split()
    clusters = set(list(map(int, clusters)))
    
    def incCluster(x):
        if x in clusters:
            return 'Y'
        else:
            return 'N'
    
    df['cluster_bool'] = df['c_label'].apply(lambda x:incCluster(x))
    
    return df

def stackedBar(df,filtered):
    
    import pandas as pd
    from bokeh.plotting import figure,show
    from bokeh.io import output_notebook,output_file
    from bokeh.models import SingleIntervalTicker, LinearAxis
    output_notebook()
    
    '''return stacked bar viz with filter parameters returned as highlighted
    two arguments: dataframe and filtered = True/False to call highlight'''
    
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
        column_filter = input('df filter column:')
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

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    
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
        x_lower_lim,x_upper_lim = borderLimits(x,max_x_coord)
        y_lower_lim,y_upper_lim = borderLimits(y,max_y_coord)
        
        image[x_lower_lim:x_upper_lim,y_lower_lim:y_upper_lim] = borderPad(x_lower_lim,x_upper_lim,y_lower_lim,y_upper_lim)
        
        return image
    
    for i in coords:
        new_image = singleMask(image,i[0],i[1])
    
    return new_image

