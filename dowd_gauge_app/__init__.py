# dependencies
# from flask import Flask, render_template, request, url_for
from flask import Flask, render_template, url_for
import json
import plotly

#-----------------------------------------------------------------------------
# App initialization

app = Flask(__name__)

#-----------------------------------------------------------------------------
# local modules
import gauge_utils

#-----------------------------------------------------------------------------
# VIEWS

@app.route('/')
def index():

    # create page items should retur a dictionary with an info message string
    # and two charts.
    page_items_dict = gauge_utils.create_page_items()

    # unpack it for clarity of what the objects are
    text_update = page_items_dict['text_info']
    dowd_fig = page_items_dict['dowd_hydrograph']
    # multi_fig = page_items_dict['multi_hydrograph']
    upper_eagle_fig = page_items_dict['upper_eagle_hydrograph']
    lower_eagle_fig = page_items_dict['lower_eagle_hydrograph']
    colorado_fig = page_items_dict['colorado_hydrograph']
    # print(text_update)
    # print("dowd figure code is: ")
    # print(dowd_fig)

    dowdJSON = json.dumps(dowd_fig, cls=plotly.utils.PlotlyJSONEncoder)
    # multiJSON = json.dumps(multi_fig, cls=plotly.utils.PlotlyJSONEncoder)
    upperEagleJSON = json.dumps(upper_eagle_fig, cls=plotly.utils.PlotlyJSONEncoder)
    lowerEagleJSON = json.dumps(lower_eagle_fig, cls=plotly.utils.PlotlyJSONEncoder)
    coloradoJSON = json.dumps(colorado_fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',
                            text_update=text_update,
                            dowdJSON=dowdJSON,
                            # multiJSON=multiJSON,
                            upperEagleJSON=upperEagleJSON,
                            lowerEagleJSON=lowerEagleJSON,
                            coloradoJSON=coloradoJSON
                            )

#-----------------------------------------------------------------------------

# if using the package style format for a flask app, this code is
# called in 'app.py' at the root level of the project and this file is renamed
# to __init__.py

# if __name__ == '__main__':
#     app.run(debug=True)
