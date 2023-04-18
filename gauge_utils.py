from datetime import datetime as dt, timedelta, timezone
import dataretrieval.nwis as nwis
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

#----------------------------------------------------------------------------
UPPER_EAGLE_GAUGE_LIST = ['09067020', '09064600', '09066510', '09065100']
LOWER_EAGLE_GAUGE_LIST = ['394220106431500', '09070000']
COLORADO_GAUGE_LIST = ['09058000', '09060799', '09070500']

#-----------------------------------------------------------------------------
# Functions used here within gauge_utils.py to make api calls, manipulate
# data, and build charts.
def get_usgs_data(gauge_list):

    '''use the dataretrieval package to get gauge data and return a data frame'''

    # create date strings for today back to 7 days ago
    end_date = dt.today().strftime('%Y-%m-%d')
    start_date = (dt.today() - timedelta(7)).strftime('%Y-%m-%d')
    param_cd = '00060'

    print(f'Calling data for {gauge_list} for {start_date} to {end_date}')
    try:
        df = nwis.get_record(sites=gauge_list,
                             service='iv',
                             parameterCd=param_cd,
                             start=start_date,
                             end=end_date
                             ).reset_index().iloc[:,:3]
    except:
        df = None

    # if a dataframe is returned successfully from USGS, do some formatting
    if df is not None:
        df.replace(-999999.0, pd.to_numeric('x', errors='coerce'), inplace=True)
        df.rename(columns={'00060':'q'}, inplace=True)

    return df


def reformat_data(df):

    ''' pivot dataframe to wideform '''

    dfw = df.pivot(index= 'datetime',
             columns='site_no',
             values='q' )

    return dfw


def estimate_dowd_level(dfw):

    ''' estimate Dowd Chute level using both equations for the 3 upstream gauges
    and for downstream gauge at avon'''

    print('estimating levels...')

    # ols linear resgression fit
    # dfw['dowd_pred_up'] = round(0.0032415 * (dfw['09064600']+dfw['09065100']+dfw['09066510']) + 0.01419, 2)
    # dfw['dowd_pred_down'] = round(0.0027584 *dfw['09067020'] + 0.1674, 2)

    # 3rd order polynomial regression fit
    #dfw['dowd_pred_down'] = round( -1.42 + 0.00915*dfw['09067020'] - 0.00000702*dfw['09067020']**2 + 0.0000000023 * dfw['09067020']**3, 2)
    # 4th order fit with some better high water data points
    dfw['dowd_pred_down'] = round( -1.5 + 0.0109*dfw['09067020'] - 0.0000123*dfw['09067020']**2 + 0.00000000761 * dfw['09067020']**3 - 0.00000000000171 * dfw['09067020']**4, 2)
    # print('estimated dowd levels dataframe:')
    # print(dfw.tail())
    return dfw

#-----------------------------------------------------------------------------
# Functions used in app.py to return outputs for visualization

def get_text_levels(dfw):

    '''function to return text output for current level information to display
    on website. It should return a dictionary with:
    current level with timestamp,
    change in last hour,
    levels at all other nearby gauges '''

    # get last reading and subtract one hour from it
    try:
      timestamp_last_reading = dfw[~dfw['dowd_pred_down'].isna()].index.max()
      timestamp_hour_before_last = timestamp_last_reading - timedelta(hours=1)
      last_reading = dfw[dfw.index == timestamp_last_reading]['dowd_pred_down'].item()
      change_last_hour = dfw[dfw.index == timestamp_last_reading]['dowd_pred_down'].item() - dfw[dfw.index == timestamp_hour_before_last]['dowd_pred_down'].item()
      change_last_hour = str(round(change_last_hour, 2))
    except:
      change_last_hour = 'not available'

    # get yesterday's max and min
    try:
        yesterday_data = dfw.loc[(timestamp_last_reading - timedelta(1)).strftime('%Y-%m-%d')]
        peak_flow = round(yesterday_data['dowd_pred_down'].max(),1)
        min_flow = round(yesterday_data['dowd_pred_down'].min(),1)

        # get the index value at the max and min flows (returns first row if more than one row is returned)
        peak_time = yesterday_data['dowd_pred_down'].idxmax()
        min_time =  yesterday_data['dowd_pred_down'].idxmin()

        yesterday_msg = (f"Yesterday's <strong>peak</strong> level of <strong>{peak_flow}&apos;</strong> occurred at {peak_time.strftime('%I:%M %p')},<br>"
                        f"Yesterday's <strong>low</strong> level of <strong>{min_flow}&apos;</strong> occurred at {min_time.strftime('%I:%M %p')}")

    except:
        yesterday_msg = "Info on yesterday's min/max not available"

    return [round(last_reading,1), timestamp_last_reading.strftime('%I:%M %p'), change_last_hour, yesterday_msg]


def build_dowd_level_chart(dfw):

    ''' create a hydrograph of estimated levels at dowd for last 7 days'''

    print("\nBuilding Dowd chart\n")

    fig = px.line(dfw,
                  x=dfw.index,
                  y=dfw.dowd_pred_down,
                  labels={
                         "datetime": "",
                         "dowd_pred_down": "Feet",
                     },
                  title="Estimated Level</i>")

    fig.update_traces(line=dict(color="Blue", width=2))

    y_max = dfw['dowd_pred_down'].max()
    y_min = dfw['dowd_pred_down'].min()

    fig.add_hrect(y0=6, y1=8, line_width=0, fillcolor="purple", opacity=0.25)
    fig.add_hrect(y0=4, y1=6, line_width=0, fillcolor="red", opacity=0.25)
    fig.add_hrect(y0=2, y1=4, line_width=0, fillcolor="yellow", opacity=0.25)
    fig.add_hrect(y0=0, y1=2, line_width=0, fillcolor="green", opacity=0.25)
    fig.add_hrect(y0=y_min-0.5, y1=0, line_width=0, fillcolor="grey", opacity=0.25)

    fig.add_hline(y=0.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=1.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=2.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=3.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=4.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=5.5, line_width=0.5, line_dash="dash", line_color="white", opacity=0.5)

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Tahoma"
        )
    )

    # print("plotly express hovertemplate:", fig.data[0].hovertemplate)
    fig.update_traces(hovertemplate="%{y:.1f} '<br>%{x|%I:%M %p}")

    # fig.update_yaxes(tick0=0, dtick=0.5)
    fig.update_yaxes(tickvals=[0,1,2,3,4,5,6,7,8,9,10,11],
                     ticks="outside",
                     ticklen=5)
    fig.update_layout(yaxis_range=[min(y_min-0.5,0), max(y_max+1,5)]) #keep the y axis at 0-5 feet unless water is really high or low
    fig.update_layout(title_x=0.5) #center title
    fig.update_xaxes(
        tickformat="%m-%d",
        tickangle = 67.5
        )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20)
        )
    config = {'displayModeBar': False}

    return fig


def build_area_gauges_chart(df, title_text):

    '''return a plotly chart of hydrograph for all gauges for last 7 days'''

    print(f"\nBuilding multi-gauge chart for {title_text}")

    plot_df = df
    # rename the site number columes with common local names
    # create plain-named aliases for gauges
    name_dict = {'09067020':'Eagle @ Avon      ',
                 '09064600':'Eagle @ Tigiwon Rd',
                 '09066510':'Gore @ Mouth      ',
                 '09065100':'Cross Cr @ Mouth  ',
                 '394220106431500':'Eagle @ Wolcott',
                 '09070000': 'Eagle @ Gypsum',
                 '09058000': 'Colorado @ Gore Canyon',
                 '09060799': 'Colorado @ Catamount',
                 '09070500': 'Colorado blw Dotsero<br>(Shoshone)'
    }

    plot_df = plot_df.replace({"site_no": name_dict})
    print('\nplot datarame:\n')
    print(plot_df.tail())

    # make the plot

    # create lists of formatted dates for x-axis so that axis and hovertemplate can be formatted separately
    # end_date = dt.today().strftime('%Y-%m-%d')
    # start_date = (dt.today() - timedelta(7)).strftime('%Y-%m-%d')
    end_date = dt.today()
    start_date = (dt.today() - timedelta(7))
    # print(f'start: {start_date, end_date}')

    # xtickvals = [dt.datetime(date) for date in range(start_date, end_date)]
    xtickvals = [(start_date + timedelta(days = day)) for day in range(7)]
    # print(xtickvals)

    xticktext = [val.strftime('%m-%d') for val in xtickvals]
    # print(xticktext)

    fig = px.line(plot_df,
              x="datetime",
              y="q",
              color='site_no',
              labels={
                  "datetime": "",
                  "q": "Flow (cfs)",
                  },
              title=f"{title_text} Gauges",
              )
    
    # hover controls and settings
    fig.update_traces(hovertemplate="%{y:.0f} cfs")
    fig.update_layout(hovermode="x unified")
    # legend formatting options
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor='top',
        y=-0.2,
        xanchor="right",
        x=1,
        title_text='',
    ))
    #center title
    fig.update_layout(
        title_x=0.5,
    )
    # format x-axis dates
    fig.update_xaxes(
        tickformat="%m-%d %H:%M",
        tickangle = 67.5,
        ticktext=xticktext,
        tickvals=xtickvals
    )
    # decrease the paper margin space around ove the plot to bring the title closer
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20)
        )
    fig.update_layout({
        'plot_bgcolor': 'rgba(204,209,217,0.25)'
        })
    
    return fig

#-----------------------------------------------------------------------------
# Control flow

def create_page_items():

    # merge the gauge lists to make a single API call
    GAUGE_LIST = UPPER_EAGLE_GAUGE_LIST + LOWER_EAGLE_GAUGE_LIST + COLORADO_GAUGE_LIST

    # add code here to see if the data file exists/has been re-created within the last hour,
    # if so, load it from the saved file, if not make a new API call for updated data
    # 1) check timestamp of last update
    # 2) if it is within last hour, load it into 'gauge_data'
    # 3) if it is older, get updated data; or perhaps last 30 mins

    gauge_data = get_usgs_data(GAUGE_LIST)

    # subset the returned gauge dataframe into individual dataframes for different charts
    try:
        upper_eagle_data = gauge_data.loc[gauge_data['site_no'].isin(UPPER_EAGLE_GAUGE_LIST)]
    except:
        upper_eagle_data = None

    try:
        lower_eagle_data = gauge_data.loc[gauge_data['site_no'].isin(LOWER_EAGLE_GAUGE_LIST)]
    except:
        lower_eagle_data = None

    try:
        colorado_data = gauge_data.loc[gauge_data['site_no'].isin(COLORADO_GAUGE_LIST)]
    except:
        colorado_data = None


    # try:
    #     wide_data = reformat_data(gauge_data)
    #     # wide_data = estimate_dowd_level(wide_data)
    # except:
    #     wide_data = None

    # try:
    #     text_info = get_text_levels(wide_data)
    # except:
    #     text_info = None
    # print('\ntext info:\n')
    # print(text_info)

    try:
        dowd_data = gauge_data.loc[gauge_data['site_no']=='09067020']
        dowd_data_wide = reformat_data(dowd_data)
        dowd_data_wide = estimate_dowd_level(dowd_data_wide)
        dowd_hydrograph = build_dowd_level_chart(dowd_data_wide)
        text_info = get_text_levels(dowd_data_wide)
    except:
        dowd_hydrograph = None
        text_info = ['<err>','<err>','<err>','<err>']

    # try:
    #     multi_hydrograph = build_area_gauges_chart(gauge_data)
    # except:
    #     multi_hydrograph = None
    
    try:
        upper_eagle_hydrograph = build_area_gauges_chart(
            upper_eagle_data, 
            title_text='Upper Eagle'
            )
    except:
        upper_eagle_hydrograph = None

    try:
        lower_eagle_hydrograph = build_area_gauges_chart(
            lower_eagle_data, 
            title_text='Lower Eagle')
    except:
        lower_eagle_hydrograph = None
    
    try:
        colorado_hydrograph = build_area_gauges_chart(
            colorado_data, 
            title_text='Upper Colorado')
    except:
        colorado_hydrograph = None


    return {'text_info': text_info,
            'dowd_hydrograph': dowd_hydrograph,
            # 'multi_hydrograph': multi_hydrograph,
            'upper_eagle_hydrograph': upper_eagle_hydrograph,
            'lower_eagle_hydrograph': lower_eagle_hydrograph,
            'colorado_hydrograph': colorado_hydrograph,
            }
