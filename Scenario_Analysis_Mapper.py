#!/usr/bin/env python
# coding: utf-8
#!/usr/bin/env python
# coding: utf-8
import json, math, copy, sys, re
import pandas as pd
import shapely.wkt
import shapely.geometry
from datetime import datetime, timezone
from datetime import timedelta
from dateutil import tz
from pathlib import Path
import urllib.parse
import webbrowser
import os
import pprint
from sklearn.preprocessing import minmax_scale
import numpy as np
from scipy import stats
# from notebook import notebookapp
from jupyter_server import serverapp
from IPython.core.display import display, HTML
from IPython.display import Javascript
import geopandas as gpd
import rpy2.robjects as ro
from rpy2.robjects import r, pandas2ri
import collections
from IPython.display import clear_output
from ipywidgets import Layout, Button, Box, FloatText, Textarea, Dropdown, Label, IntSlider, RadioButtons, VBox, HBox, Text, BoundedIntText
import ipywidgets as widgets

## Retrieve Server URL that Jupyter is running

jupyter_envs = {k: v for k, v in os.environ.items() if k.startswith('JUPYTER')}
temp_server = jupyter_envs['JUPYTER_INSTANCE_URL']

# Define Paths for Visualization (Jupyter Lab)
servers = list(serverapp.list_running_servers())
servers1 = temp_server+servers[0]["base_url"]+ 'view'
servers2 = temp_server+servers[0]["base_url"]+ 'edit'
servers3 = temp_server+servers[0]["base_url"]+ 'files'

## Define Paths for Visualization (Julyter Notebook)
# servers = list(notebookapp.list_running_servers())
# servers1 = temp_server+servers[0]["base_url"]+ 'view'
# servers2 = temp_server+servers[0]["base_url"]+ 'edit'

cwd = os.getcwd()
prefix_cwd = "/home/jovyan/work"
cwd = cwd.replace(prefix_cwd, "")

# # This is for Jupyter notebook installed in your PC
# local_dir1 = cwd
# local_dir2 = cwd

# This is for CyberGISX. Uncomment two command lines below when you run in CyberGIX Environment
local_dir1 = servers1 + cwd + '/'
local_dir2 = servers2 + cwd + '/'
local_dir3 = servers3 + cwd + '/'


def write_INDEX_html(param, oDir):
    #open Adaptive_Choropleth_Mapper.html (the excutable file for the visualization)
    ifile = open("template/Adaptive_Choropleth_Mapper.html", "r", encoding="utf-8")
    contents = ifile.read()
    
    #Replace variables based on the user's selection in each of four files below.
    contents = contents.replace("Adaptive Choropleth Mapper", param['title'])
    contents = contents.replace("data/CONFIG.js", "data/CONFIG_"+param['filename_suffix']+".js")
    contents = contents.replace("data/GEO_JSON.js", "data/GEO_JSON_"+param['filename_suffix']+".js")
    contents = contents.replace("data/VARIABLES.js", "data/VARIABLES_"+param['filename_suffix']+".js")
    
    #write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
    ofile = open(oDir+"/index.html", "w", encoding="utf-8")
    ofile.write(contents)
    ofile.close()
    #print (contents)    

   
def write_CONFIG_js(param, oDir):
    # read ACM_GEO_CONFIG.js
    ifile = open("template/SAM_CONFIG.js", "r", encoding="utf-8")
    contents = ifile.read()
    
    # get valid varables from contents
    vlist = re.findall(r'(\nvar +(\S+) *= *(.+))', contents)
    # vlist = [ ('\nvar Subject = "";', 'Subject', '"";')
    #           ('\nvar NumOfMaps = 2;', 'NumOfMaps', '2;')
    #           ('\nvar NumOfPCP = 7;', 'NumOfPCP', '7;')
    #           ('\nvar NumOfCLC = 7;', 'NumOfCLC', '7;')
    #           ('\nvar NumOfMLC = 4;', 'NumOfMLC', '4;')
    #           ...                                         ]
    
    # replace the value of the file to the value in the parameter 
    vdict = {vtuple[1]: vtuple for vtuple in vlist}
    for i, (key, value) in enumerate(param.items()):
        if (key in vdict):
            jstatement = '\nvar ' + key + ' = ' + json.dumps(value) + ';'           # create js statement
            contents = contents.replace(vdict[key][0], jstatement)
    '''
    NumOfMaps = param['NumOfMaps']
    # Automatically set Map_width, Map_height. 
    Map_width = "720px"
    Map_height = "400px"
    if (NumOfMaps <= 4):
        Map_width = "400px"
        Map_height = "400px"
    if (NumOfMaps <= 3):
        Map_width = "450px"
        Map_height = "400px"
    if (NumOfMaps <= 2):
        Map_width = "720px"
        Map_height = "400px"
    if (NumOfMaps <= 1):
        Map_width = "720px"
        Map_height = "400px"
        
    Map_width = 'var Map_width  = "' + Map_width + '";'
    Map_height = 'var Map_height = "' + Map_height + '";'

    contents = contents.replace('var Map_width = "720px";', Map_width)
    contents = contents.replace('var Map_height = "400px";', Map_height)
    '''
    #Write output including the replacement above
    filename_GEO_CONFIG = oDir + "/data/CONFIG_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_CONFIG, 'w', encoding="utf-8")
    ofile.write(contents)
    ofile.close()    
    #print (contents)          
    
    
def findOutliers(array, outliersDict, col):
    Q1 = np.percentile(array, 25)
    Q3 = np.percentile(array, 75)
    IQR = Q3 - Q1
    
    lowerBound = Q1 - 1.5*IQR
    upperBound = Q3 + 1.5*IQR
    
    for i, val in enumerate(array):
        if val < lowerBound or val > upperBound:
            outliersDict[i].append(col)
    
    return

    
    
def write_VARIABLES_js(param, oDir, excludeOutliers):
    #if ('Sequence' not in param or not param['Sequence']): df_pivot.drop(columns=['Sequence'], inplace=True)
    #df_pivot = pd.read_csv(param["inputCSV"])
    
    ro.r('''source('forecast_func.R')''')
    #return
    pandas2ri.activate()
    forecast_func = ro.globalenv['forecast_func']
    forecast_param = param['Scenario'] if ('Scenario' in param) else {}
    if ('inputCSV' in param): forecast_param['var_file'] = param['inputCSV']
    data_wide = forecast_func(**forecast_param)
    if ('Scenario' in param):
       #data_wide = forecast_func(var_names=param['Scenario']['var_names'], var_muls=param['Scenario']['var_muls'])
       #data_wide = forecast_func(var_file=param['Scenario']['var_file'], var_muls=None)
       data_wide = forecast_func(**param['Scenario'])
    else:
       data_wide = forecast_func()

    # Convert FIPS code to string to have leading zeros (e.g., 1111 -> 01111)
    data_wide['FIPS'] = data_wide['FIPS'].astype(str)
    data_wide['FIPS'] = data_wide.apply(lambda x: '0'+ x['FIPS'] if len(x['FIPS']) == 4 else x['FIPS'], axis=1)
    data_wide.to_excel(f"./{oDir}/data/{oDir}_output.xlsx") # Will be saved as a excel file in the output directory
    
    columnsList = data_wide.columns.values.tolist()
    valuesList = data_wide.values.tolist()
    #print(columnsList)
    #print(valuesList[:2])
    heading1 = ['geoid']
    heading2 = ['']
    for i, col in enumerate(columnsList[1:]):
        #if (i == 0): continue
        p = col.rfind('.')
        s1 = col
        s2 = "0000"
        if (p >= 0):
            s1 = col[:p]
            s2 = col[p+1:]
        #print(i, s1, s2)
        heading1.append(s1)
        heading2.append(s2)
    #print(heading1)
    #print(heading2)
    
    # change heading1 from code to text human readable.
    if ('easy2read' in param):
        for i, h1 in enumerate(heading1):
            if (h1 in param['easy2read']): heading1[i] = param['easy2read'][h1]
    #print(heading1)
    
    heading = ['geoid']
    for i in range(len(heading1)):
        if (i == 0): continue
        heading.append(heading2[i] + '_' + heading1[i])
    #print(heading)
    
    # write df_wide to GEO_VARIABLES.js
    filename_GEO_VARIABLES = oDir + "/data/VARIABLES_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_VARIABLES, 'w')
    ofile.write('var GEO_VARIABLES =\n')
    ofile.write('[\n')
    #ofile.write('  '+json.dumps(heading1)+',\n')
    #ofile.write('  '+json.dumps(heading2)+',\n')
    ofile.write('  '+json.dumps(heading)+',\n')
    
    wCount = 0
    #for i, row in df_pivot.reset_index().iterrows():
    outliersDict = collections.defaultdict(list)
    
    if excludeOutliers:
        for idx, col in enumerate(columnsList[1:]):
            findOutliers(np.asarray(data_wide[col]), outliersDict, idx+1)
        
    
    for i, row in data_wide.iterrows():        
        aLine = row.tolist()
        #for j, col in enumerate(aLine[2:], 2):
        #    try:
        #        aLine[j] = int(col)                                  # convert float to int
        #    except ValueError:
        #        aLine[j] = -9999                                     # if Nan, set -9999
        aLine[0] = int(aLine[0])
            
        for j, col in enumerate(aLine):
            if (j == 0): continue
            if (math.isinf(col)) or j in outliersDict[wCount]:
                aLine[j] = -9999                      # if Infinity or outlier, set -9999
            
        wCount += 1 
        ofile.write('  '+json.dumps(aLine)+',\n')
    
    #print("GEO_VARIABLES.js write count:", wCount)
    ofile.write(']\n')
    ofile.close()


def write_GEO_JSON_js(param, oDir):    
    # read shape file to df_shape
    df_shapes = gpd.read_file(param['shapefile'])
    
    #df_shapes = df_shapes.rename(columns={'GEOID10': 'geoid'})
    #df_shapes = param['shapefile']
    #print(df_shapes.dtypes)
    df_shapes = df_shapes.astype(str)
    #print(df_shapes.dtypes)
    #print(df_shapes)
    
    geoid = df_shapes.columns[0]
    name = df_shapes.columns[1]
    #print(geoid, name)
    
    df_shapes = df_shapes[pd.notnull(df_shapes['geometry'])]
    
    # open GEO_JSON.js write heading for geojson format
    filename_GEO_JSON = oDir + "/data/GEO_JSON_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_JSON, 'w')
    ofile.write('var GEO_JSON =\n')
    ofile.write('{"type":"FeatureCollection", "features": [\n')
    
    #Convert geometry in GEOJSONP to geojson format
    wCount = 0
    for shape in df_shapes.itertuples():
        feature = {"type":"Feature"}
        if (type(shape.geometry) is float):								# check is NaN?
            #print(tract.geometry)
            continue
        #print(tract.geometry)
        aShape = shapely.wkt.loads(shape.geometry)
        #print(type(shape))
        #print(shape.geoid)
        #print(shape.name)
        feature["geometry"] = shapely.geometry.mapping(aShape)
        #feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
        feature["properties"] = {geoid: shape.geoid, name: shape.name}
        wCount += 1
        ofile.write(json.dumps(feature)+',\n')
    #print("GEO_JSON.js write count:", wCount)
    # complete the geojosn format by adding parenthesis at the end.	
    ofile.write(']}\n')
    ofile.close()


# write param.log file from param into the new folder of result
def write_LOG(param, oDir):
    # convert param to pretty print data structures
    #print(param)
    contents = pprint.pformat(param, compact=True, sort_dicts=False)        # depth=1, 
    
    #write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
    ofile = open(oDir+"/data/param.log", "w")
    create_at = datetime.now()
    ofile.write('%s %s\n\n' % (create_at.strftime('%Y-%m-%d %H:%M:%S'), oDir))
    ofile.write('  '+contents.replace('\n', '\n  '))
    ofile.close()


def Scenario_Analysis_log(param):
    #Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
    oDir = 'SAM_' + param['filename_suffix']
    path = Path(oDir + '/data')
    path.mkdir(parents=True, exist_ok=True)
    
    # build array of logs from directory of 'SAM_'
    logs = []
    dirname = os.getcwd()
    subnames = os.listdir(dirname)
    for subname in subnames:
        fullpath = os.path.join(dirname, subname)
        #print(local_dir1+fullpath)
        if (not os.path.isdir(fullpath)): continue
        if (not subname.startswith('SAM_')): continue
        #print(os.path.join(fullpath, 'index.html'))
        indexfile = os.path.join(fullpath, 'index.html')
        logfile = os.path.join(fullpath, 'data/param.log')
        if (not os.path.exists(indexfile)): continue
        if (not os.path.exists(logfile)): continue
        #print(fullpath, logfile)
        # read param.log
        ifile = open(logfile, "r")
        wholetext = ifile.read()
        contents = wholetext.split('\n', maxsplit=1)
        if (len(contents) != 2): continue
        cols = contents[0].split(' ', maxsplit=3)
        #create_at = contents[0] if (len(cols) <= 2) else cols[0] + ' ' + cols[1] + ' &nbsp; ' + cols[2]
        create_at = contents[0]
        out_dir = ""
        if (len(cols) >= 3): 
            create_at = cols[0] + ' ' + cols[1]
            out_dir = cols[2]
        create_at = datetime.fromisoformat(create_at).replace(tzinfo=timezone.utc)
        param = contents[1]
        #print(subname+'/'+'index.html')
        #print(create_at)
        #print(param)
        #logs.append({'indexfile': subname+'/'+'index.html', 'create_at': create_at, 'out_dir': out_dir, 'param': param})
        #logs.append({'indexfile': local_dir1+subname+'/'+'index.html', 'create_at': create_at, 'out_dir': out_dir, 'param': param})
        logs.append({'indexfile': local_dir1+'/'+subname+'/'+'index.html', 'create_at': create_at.isoformat(), 'out_dir': out_dir, 'param': param})
    logs = sorted(logs, key=lambda k: k['create_at']) 
    #print(logs)
    
    #Write output to log.html
    filename_LOG = "log.html"
    ofile = open(filename_LOG, 'w')
    ofile.write('<!DOCTYPE html>\n')
    ofile.write('<html>\n')
    ofile.write('<head>\n')
    ofile.write('  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
    ofile.write('  <title>Neighborhood Analysis Logging</title>\n')
    ofile.write('</head>\n')
    ofile.write('<body>\n')
    ofile.write('  <header>\n')
    ofile.write('    <h1>Logging</h1><p style="color:#6495ED;"><i>*Copy the URL using the button and paste it to your browser to see visualizations you created before.</i></p>\n')
    ofile.write('  </header>\n')
    
    for idx, val in enumerate(logs):
        params = val['param'].split('\n')
        html = '\n'
        html += '<div style="margin:10px; float:left; border: 1px solid #99CCFF; border-radius: 5px;">\n'
        html += '  <table>\n'
        html += '    <tr>\n'
        html += '      <td>\n'
        html += '      <span style="color:#CD5C5C;"><strong>' + str(idx+1) + '. ' + val['out_dir'] + '</strong></span>'
        html += '        <span style="display: inline-block; width:380px; text-align: right;">' + '<span class="utcToLocal">'+ val['create_at'] + '</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'        
        html += '        <input type="text" value=' + val['indexfile']+ ' id="myInput' + str(idx+1) + '">'
        html += '        <button onclick="myFunction' + str(idx+1) + '()">Copy</button></span>\n'        
        html += '      </td>\n'
        html += '    </tr>\n'
        html += '    <tr>\n'
        html += '      <td>\n'
        html += '<pre>\n'
        for param in params:
            html += param + '\n'
        html += '</pre>\n'
        html += '      </td>\n'
        html += '    </tr>\n'
        html += '  </table>\n'
        html += '</div>\n'
        
        html += '<script>'
        html += 'function myFunction' + str(idx+1) + '() {'
        html += '  var copyText = document.getElementById("myInput' + str(idx+1) + '");' #Get the text field
        html += '  copyText.select();'                                 #Select the text field
        html += '  copyText.setSelectionRange(0, 99999);'              #For mobile devices
        html += '  navigator.clipboard.writeText(copyText.value);'     #Copy the text inside the text field
        html += '  alert("The URL has been copied to the clipboard. Paste it to the browser to see your visualizations: " + copyText.value);'       #Alert the copied text
        html += '};'
        html += 'document.querySelectorAll(".utcToLocal").forEach('
        html += '  function (i) {'
        html += '    const options = {hour12: false, hour:"2-digit", minute:"2-digit", timeZoneName: "short", year: "numeric", month: "numeric", day: "numeric"};'
        html += '    i.innerHTML = new Date(i.innerText).toLocaleString("en-US",options);'
        html += '  }'
        html += ');'
        html += '</script>\n'
        ofile.write(html)   
    ofile.write('</body>\n')
    ofile.write('</html>')
    ofile.close()
    
    local_dir = os.path.dirname(os.path.realpath(__file__))
    #local_dir = os.getcwd()
    fname =urllib.parse.quote(filename_LOG)
    url = 'file:' + os.path.join(local_dir, fname)
    #url = os.path.join(template_dir, fname)    
    webbrowser.open(url)


def Scenario_Analysis(param, excludeOutliers):
    #Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
    oDir = 'SAM_' + param['filename_suffix']
    path = Path(oDir + '/data')
    path.mkdir(parents=True, exist_ok=True)
    
    print('output directory :  {}'.format(oDir))
    print('Creating Visualization ... ')
    write_INDEX_html(param, oDir)
    write_CONFIG_js(param, oDir)
    write_VARIABLES_js(param, oDir, excludeOutliers)
    write_GEO_JSON_js(param, oDir)
    write_LOG(param, oDir)
        
    #print(local_dir)
    fname =urllib.parse.quote('index.html')
    template_dir = os.path.join(local_dir1, 'SAM_' + param['filename_suffix'])
    #url = 'file:' + os.path.join(template_dir, fname)
    url = os.path.join(template_dir, fname)    
    webbrowser.open(url)
    print(f'Visualization: {url}')
    print(f"Log: {local_dir1 + '/log.html'}")
    print(f"Advanced Parameters: {local_dir2 + 'SAM_' + param['filename_suffix']+'/data/CONFIG_' + param['filename_suffix']+'.js'}")
    print(f"Download Results: {local_dir3 + 'SAM_' + param['filename_suffix']+'/data/SAM_' + param['filename_suffix']+'_output.xlsx'}")

    # Following line will pop up 'index.html' when the code runs (Only works in Jupyter Lab).
    # display(Javascript('window.open("{url}");'.format(url=url)))


# Display GUI
def Display_GUI():    

    form_item_layout = Layout(
    display='flex',
    flex_flow='row',
    width='500px',
    justify_content='space-between'
    )

    initiallayers = ["2012_HIV Rate", "2013_HIV Rate", "2014_HIV Rate",
               "2015_HIV Rate", "2016_HIV Rate", "2017_HIV Rate",
               "2018_HIV Rate", "2019_HIV Rate", "2020_HIV Rate",
               "2021_HIV Rate", "2022_HIV Rate", "2023_HIV Rate",
               "2024_HIV Rate", "2025_HIV Rate", "2026_HIV Rate"]

    # Basic parameters
    basic = VBox([
        Box([Label(value='How do you want to name the result?', layout=Layout(width="300px")),
            Text(value="HIV")], layout=form_item_layout),
    
        Box([Label(value='Variable'), Label(value='Weight')], layout=form_item_layout),
    
        VBox([HBox([Label(value='Opioid Prescriptions', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='% People as Food Stamp/SNAP Recipients', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='% POP in Juvenille Facilities', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='Federally Qualified Health Centers', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='NHSC Primary Care sites', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='Knowledge of HIV Status', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='HCV Death', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='HIV Test', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='Community Mental Health Centers', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='PrEP Use', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='% of Households with Social Security Income', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='Illicit Drug Use Rate', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),
            HBox([Label(value='Linkage to HIV Care', layout=Layout(width="450px")),
            BoundedIntText(min=1, max=10, value=1, layout=Layout(width="50px"))]),],
            layout=Layout(width='500px', border='dashed 1px')),
    
        Label(value=""),
        
        Box([Label(value='What do you want to visualize?', layout=Layout(width="300px")), 
            RadioButtons(options=["Multiple Line Chart", "Comparison Line Chart", "Parallel Coordinates Plot", 
                                  "No Extra Plot"])],
            layout=form_item_layout),
    ])

    # Advanced parameters
    optional = VBox([
        Box([Label(value='Title', layout=Layout(width="300px")),
            Textarea(value="HIV Scenario Analysis from 2012 to 2026, United States", layout=Layout(width="221px"))], 
            layout=form_item_layout),
    
        Box([Label(value='Subject', layout=Layout(width="300px")),
            Text(value="Temporal Patterns")], layout=form_item_layout),
    
        Box([Label(value='Shapefile Path', layout=Layout(width="300px")),
            Text(value="shp/US/counties.shp")], layout=form_item_layout),
    
        Box([Label(value='CSV File', layout=Layout(width="300px")),
            Text(value="data_imputedx_forecast.csv")], layout=form_item_layout),
        
        Box([Label(value='Number of Maps', layout=Layout(width="300px")),
            BoundedIntText(value=2, min=1, max=10)], layout=form_item_layout),
    
        Box([Label(value='Map 1: Select Variable and Year', layout=Layout(width = "300px")),
            Dropdown(options=initiallayers)], layout=form_item_layout),
    
        Box([Label(value='Map 2: Select Variable and Year', layout=Layout(width = "300px")),
            Dropdown(options=initiallayers, value="2026_HIV Rate")], layout=form_item_layout),
    
        Box([Label(value='Initial Map Center (lat, lon)', layout=Layout(width="300px")),
            Text(value="37, -97")], layout=form_item_layout),
    
        Box([Label(value='Initial Map Zoom Level', layout=Layout(width="300px")), 
            IntSlider(min=1, max=10, value=4)], layout=form_item_layout),
        
        Box([Label(value='Map Width', layout=Layout(width="221px")),
            BoundedIntText(min=350, max=1500, value=650, layout=Layout(width="80px")), 
            Label(value='Pixels', layout=Layout(display='flex', width="50px"))]),
    
        Label(value='Change Names of Variables:'),
    
        VBox([HBox([Label(value='Rate', layout=Layout(width="300px")), Text(value="HIV Rate")]),
            HBox([Label(value='opioid_prsc', layout=Layout(width="300px")), Text(value="Opioid Prescriptions")]),
            HBox([Label(value='FoodStampSNAPRecipientEstimate_r', layout=Layout(width="300px")), Text(value="% people as Food Stamp/SNAP Recipients")]),
            HBox([Label(value='PopinJuvenilleFacilities_r_l', layout=Layout(width="300px")), Text(value="% POP in Juvenille Facilities")]),
            HBox([Label(value='nFedQualifiedHealthCenters_r_l', layout=Layout(width="300px")), Text(value="Federally Qualified Health Centers")]),
            HBox([Label(value='nNHSCPrimaryCareSiteswProv_r_l', layout=Layout(width="300px")), Text(value="NHSC Primary Care sites")]),
            HBox([Label(value='knowledge', layout=Layout(width="300px")), Text(value="Knowledge")]),
            HBox([Label(value='hcv', layout=Layout(width="300px")), Text(value="HCV Death")]),
            HBox([Label(value='hivtst', layout=Layout(width="300px")), Text(value="HIV Test")]),
            HBox([Label(value='nCommunityMentalHealthCtrs_r_l', layout=Layout(width="300px")), Text(value="Community Mental Health centers")]),
            HBox([Label(value='prep_rate_l', layout=Layout(width="300px")), Text(value="PrEP Use")]),
            HBox([Label(value='HHswSupplemntlSecurityInc_r', layout=Layout(width="300px")), Text(value="% of Households with Social Security Income")]),
            HBox([Label(value='illicit_l', layout=Layout(width="300px")), Text(value="Illicit Drug Use Rate")]),
            HBox([Label(value='linkage', layout=Layout(width="300px")), Text(value="Linkage to Care")])],
            layout = Layout(width='450px', border='dashed 1px')),
    
        Label(value=""),
    
        Label(value='If Multiple Line Chart (MLC) is Displayed:'),
    
        VBox([HBox([Label(value='Number of MLC(s)', layout=Layout(width="300px")), Text(value="14")]),
            HBox([Label(value='Selected Variables', layout=Layout(width="300px")), Textarea(value='HIV Rate,'\
                           "Opioid Prescriptions,"\
                           "% people as Food Stamp/SNAP Recipients,"\
                           "% POP in Juvenille Facilities,"\
                           "Federally Qualified Health Centers,"\
                           "NHSC Primary Care sites,"\
                           "Knowledge,"\
                           "HCV Death,"\
                           "HIV Test,"\
                           "Community Mental Health centers,"\
                           "PrEP Use,"\
                           "% of Households with Social Security Income,"\
                           "Illicit Drug Use Rate,"\
                           "Linkage to Care", layout=Layout(width="221px"))]),
            HBox([Label(value='Highlight Method', layout=Layout(width="300px")), Text(value="2021,2026,#fdff32")]),
            Label(value='Note: The value of "Number of MLC(s)" should be matched with the counts'),
            Label(value='of variables in "Selected Variables".')],
            layout=Layout(width='450px', border='dashed 1px')),
    
    
        Label(value=""),
    
        Label(value='If Comparison Line Chart (CLC) is Displayed:'),
    
        VBox([HBox([Label(value='Number of CLC(s)', layout=Layout(width="300px")), Text(value="")]),
            HBox([Label(value='Selected Variables', layout = Layout(width="300px")), Textarea(value="", layout=Layout(width="221px"))]),
            Label(value='Note: The value of "Number of CLC(s)" should be matched with the counts'),
            Label(value='of variables in "Selected Variables".')],
            layout=Layout(width='450px', border='dashed 1px')),
    
        Label(value=""),
    
        Label(value='If Parallel Coordinate Plot (PCP) is Displayed:'),
    
        VBox([HBox([Label(value='Number of PCP(s)', layout=Layout(width="300px")), Text(value="9")]),
            '''
            HBox([Label(value='Selected Variables', layout=Layout(width="300px")), Textarea(value="2012_HIV Rate,2013_HIV Rate,"\
            "2014_HIV Rate,2015_HIV Rate,2016_HIV Rate,2017_HIV Rate,2018_HIV Rate,2019_HIV Rate,2020_HIV Rate,2021_HIV Rate,2022_HIV Rate,"\
            "2023_HIV Rate,2024_HIV Rate,2025_HIV Rate,2026_HIV Rate", layout=Layout(width="221px"))]),
            '''
            HBox([Label(value='Selected Variables', layout=Layout(width="300px")), Textarea(value="2013_PrEP Use,2013_HIV Rate,2013_% people as Food Stamp/SNAP Recipients,2013_HCV Death,2013_Community Mental Health centers, 2013_Federally Qualified Health Centers, 2013_NHSC Primary Care sites, 2013_Opioid Prescriptions,  2013_% POP in Juvenille Facilities", layout=Layout(width="221px"))]),            
            Label(value='Note: The value of "Number of PCP(s)" should be matched with the counts'),
            Label(value='of variables in "Selected Variables".')],
            layout=Layout(width='450px', border='dashed 1px')),
        
        Label(value=""),
        
        Box([Label(value='Top 10 Chart', layout=Layout(width="300px")), 
            RadioButtons(options=['Display', "Don't display"])], layout=form_item_layout),
        
        Box([Label(value="Exclude Outliers", layout=Layout(width="300px")),
             RadioButtons(options=['Yes', "No"], value="No")],layout=form_item_layout)
    ])


    children = [basic, optional]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, "Basic Parameters")
    tab.set_title(1, "Advanced Parameters")
    
    display(tab)
    
    # def additional_chart_change(change):
    #     if change.new == 'Multiple Line Chart':
    #         basic.children[0].children[1].value = 'HIV_MLC'
    #     elif change.new == 'Comparison Line Chart':
    #         basic.children[0].children[1].value = 'HIV_CLC'
    #     elif change.new == 'Parallel Coordinates Plot':
    #         basic.children[0].children[1].value = 'HIV_PCP'
    #     elif change.new == "Don't display":
    #         basic.children[0].children[1].value = 'HIV'
    #
    # basic.children[4].children[1].observe(additional_chart_change, names='value')
    
    submit_button = Button(description="Run Model", button_style='success')
    help_button = Button(description="I Need Help", button_style="info")
    
    buttons = HBox([submit_button, Label(value='', layout=Layout(width='20px')), help_button])
    display(buttons)
    
    # Get parameters
    output = widgets.Output()
    
    @output.capture()
    def paramsSubmit(button):
        createVisualization(basic, optional)
        return
    
    submit_button.on_click(paramsSubmit)
    
    # Help button
    @output.capture()
    def helpbuttonClicked(button):
        
        url = "https://cybergis.github.io/CyberGIS_HIV_document/build/html/index.html"
        display(Javascript('window.open("{url}");'.format(url=url)))
        return
    
    help_button.on_click(helpbuttonClicked)
        
    display(output)
    
    return

# Create visualization
def createVisualization(basic, optional):
    center = optional.children[7].children[1].value.split(",")
    variables = ["opioid_prsc", "FoodStampSNAPRecipientEstimate_r", "PopinJuvenilleFacilities_r_l",
             "nFedQualifiedHealthCenters_r_l", "nNHSCPrimaryCareSiteswProv_r_l", "knowledge",
             "hcv", "hivtst", "nCommunityMentalHealthCtrs_r_l", "prep_rate_l", "HHswSupplemntlSecurityInc_r",
             "illicit_l", "linkage"]
    weights = [x.children[1].value for x in basic.children[2].children]

    num_MLC = int(optional.children[14].children[0].children[1].value)
    num_CLC = None
    if optional.children[17].children[0].children[1].value:
        num_CLC = int(optional.children[17].children[0].children[1].value)
    num_PCP = int(optional.children[20].children[0].children[1].value)

    vars_MLC = optional.children[14].children[1].children[1].value.split(",")
    vars_CLC = optional.children[17].children[1].children[1].value.split(",")
    vars_PCP = optional.children[20].children[1].children[1].value.split(",")

    highlight_MLC = [optional.children[14].children[2].children[1].value.split(",")]


    name_dict = {}
    
    for i in range(14):
        name_dict[optional.children[11].children[i].children[0].value] = optional.children[11].children[i].children[1].value
        
    excludeOutliers = True if optional.children[23].children[1].value == "Yes" else False

    params = {
        'title': optional.children[0].children[1].value,
    
        'Subject': optional.children[1].children[1].value,
    
        'filename_suffix':  basic.children[0].children[1].value,
    
        'InitialLayers': [optional.children[5].children[1].value, optional.children[6].children[1].value],
    
        'shapefile': optional.children[2].children[1].value,
    
        'inputCSV': optional.children[3].children[1].value,
    
        'Initial_map_center': [int(x) for x in center],
    
        'Initial_map_zoom_level': optional.children[8].children[1].value,
    
        'Top10_Chart': True if optional.children[22].children[1].value == "Display" else False,
    
        'Map_width': str(optional.children[9].children[1].value) + "px",
    
        'NumOfMaps': int(optional.children[4].children[1].value),
    
        'Multiple_Line_Chart': True if basic.children[4].children[1].value == "Multiple Line Chart" else False,
    
        'Comparision_Chart': True if basic.children[4].children[1].value == "Comparison Line Chart" else False,
    
        'Parallel_Coordinates_Plot': True if basic.children[4].children[1].value == "Parallel Coordinates Plot" else False,
    
        'Scenario': {'var_names': variables, 'var_muls': weights},
    
        'easy2read': name_dict
    }

    if params["Multiple_Line_Chart"]:
        params["NumOfMLC"] = num_MLC
        params["InitialVariableMLC"] = vars_MLC
        params["HighlightMLC"] = highlight_MLC
    
    elif params["Comparision_Chart"]:
        if num_CLC:
            params["NumOfCLC"] = num_CLC
        if vars_CLC != ['']:
            params["InitialVariableCLC"] = vars_CLC
    
    elif params["Parallel_Coordinates_Plot"]:
        params["NumOfPCP"] = num_PCP
        params["InitialVariablePCP"] = vars_PCP
        
    oDir = 'SAM_' + params['filename_suffix']
    
    output = widgets.Output()
    @output.capture()
    def proceed(button):
        yes_button.disabled = True
        no_button.disabled = True
        print("Proceed.")
        
        Scenario_Analysis(params, excludeOutliers)
        Scenario_Analysis_log(params)
        return
    
    @output.capture()
    def abort(button):
        yes_button.disabled = True
        no_button.disabled = True
        print("Abort.")
        
        return
    
    if os.path.exists(oDir):
        print("Folder already exists. Will overwrite the former visualization. Proceed?")
        yes_button = Button(description="Yes", button_style='warning')
        no_button = Button(description="No", button_style='warning')
        
        buttons = HBox([yes_button, no_button])
        display(buttons)
        
        yes_button.on_click(proceed)
        no_button.on_click(abort)
        display(output)
        
    else:
        Scenario_Analysis(params, excludeOutliers)
        Scenario_Analysis_log(params)
    return

    
if __name__ == '__main__':

    started_datetime = datetime.now()
    print('Scenario_Analysis_Mapper start at %s' % (started_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    
    param_MLC = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "HIV Rate and Affecting Factors <font color='grey' size='-1'>&nbsp;&nbsp;(Highlighted Area: Predicted Values)</font>",
        'filename_suffix': "HIV_MLC",                       # max 30 character 
        'inputCSV': "data_imputedx.csv", 
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters","linkage_perc"], 'var_muls': [2,2,2]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'NumOfMaps':2,
        'Map_width':"650px",    
        'Top10_Chart': True,
        'Multiple_Line_Chart': True,
        'NumOfMLC': 4,
        'InitialVariableMLC': ['HIV Rate', 
                               'Rate of Illicit Drug Use', 
                               'Health Care Center (/100k pop)', 
                               'Viral Load Test within 1 Month of Diagnosis (/100k pop']    
    }
    
    param_CLC = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "Temporal Patterns",
        'filename_suffix': "HIV_CLC",                                       # max 30 character  
        'inputCSV': "data_imputedx.csv", 
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters", "linkage_perc"], 'var_muls': [2,2,2]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'NumOfMaps':2,
        'Map_width':"650px",      
        'Top10_Chart': True,
        'Comparision_Chart': True, 
    }
    
    param_PCP = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "HIV Rate",
        'filename_suffix': "HIV_PCP",                                      # max 30 character  
        'inputCSV': "data_imputedx.csv",     
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters", "linkage_perc"], 'var_muls': [2,2,2]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'NumOfMaps':2,
        'Map_width':"650px",      
        'Top10_Chart': True,
        'Parallel_Coordinates_Plot': True, 
    }
    
    param_Scatter = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "HIV Rate and Affecting Factors <font color='grey' size='-1'>&nbsp;&nbsp;(Highlighted Area: Predicted Values)</font>",
        'filename_suffix': "HIV_Scatter",                       # max 30 character 
        'inputCSV': "data_imputedx.csv", 
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters","linkage_perc"], 'var_muls': [5,1,1]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'Scatter_Plot':True,    
    }
    
    param_MLC1 = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "HIV Rate and Affecting Factors <font color='grey' size='-1'>&nbsp;&nbsp;(Highlighted Area: Predicted Values)</font>",
        'filename_suffix': "HIV_MLC_sample1",                       # max 30 character 
        'inputCSV': "data_imputedx.csv", 
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters","linkage_perc"], 'var_muls': [1,1,1]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'NumOfMaps':1,
        'Map_width':"1000px",
        'Top10_Chart': False,
        'Multiple_Line_Chart': True,
        'NumOfMLC': 4,
        'InitialVariableMLC': ['HIV Rate', 
                               'Rate of Illicit Drug Use', 
                               'Health Care Center (/100k pop)', 
                               'Viral Load Test within 1 Month of Diagnosis (/100k pop',]   
    }
    
    param_MLC2 = {
        'title': "HIV Scenario Analysis from 2012 to 2026, United States",
        'Subject': "HIV Rate and Affecting Factors <font color='grey' size='-1'>&nbsp;&nbsp;(Highlighted Area: Predicted Values)</font>",
        'filename_suffix': "HIV_MLC_sample2",                       # max 30 character 
        'inputCSV': "data_imputedx.csv", 
        'shapefile': 'shp/US/counties.shp',
        'Scenario': {'var_names': ["illicit", "fedqualifiedhealthcenters","linkage_perc"], 'var_muls': [5,1,1]},
        'easy2read': {'Rate': 'HIV Rate', 
                      'illicit': 'Rate of Illicit Drug Use',  
                      'fedqualifiedhealthcenters': 'Health Care Center (/100k pop)', 
                      'linkage_perc': 'Viral Load Test within 1 Month of Diagnosis (/100k pop)'},
        'NumOfMaps':1,
        'Map_width':"1000px",
        'Top10_Chart': False,
        'Multiple_Line_Chart': True,
        'NumOfMLC': 4,
        'InitialVariableMLC': ['HIV Rate', 
                               'Rate of Illicit Drug Use', 
                               'Health Care Center (/100k pop)', 
                               'Viral Load Test within 1 Month of Diagnosis (/100k pop']  
    }



    Scenario_Analysis(param_MLC)
    
    #Scenario_Analysis(param_MLC1)
    #Scenario_Analysis(param_MLC2)
    #Scenario_Analysis(param_Scatter)
    #Scenario_Analysis(param_PCP)
    #Scenario_Analysis(param_CLC)
    #Scenario_Analysis(param_MLC)


#Scenario_Analysis_log(param_MLC)
    
    ended_datetime = datetime.now()
    elapsed = ended_datetime - started_datetime
    total_seconds = int(elapsed.total_seconds())
    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)	
    print('Scenario_Analysis_Mapper ended at %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d %H:%M:%S'), hours, minutes, seconds))

else:
    pass


