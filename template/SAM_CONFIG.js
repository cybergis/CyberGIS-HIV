// Define subject of this visaulize
//var Subject = "";
var Subject = "";
var Subject_MLC = "Multiple Line Chart (MLC):  HIV rates and their key predictors over time";
var Subject_CLC = "Comparison Line Chart (CLC): Compare HIV rates between two counties";
var Subject_PCP = "Temporal Change of HIV rate across time";
var Subtext = "<font color='grey' size='-1'>&nbsp;&nbsp;(Highlighted Area: Predicted Values)</font>";

// Define the number of maps that you want to visualize. upto 15 maps are supported.
var NumOfMaps = 2;


// Define the number of variable that you want to visaulize Parallel Coordinates Plot. 
var NumOfPCP = 15;
//Define variables that you want to visualize at PCP.
var InitialVariablePCP = ["2012_HIV Rate", "2013_HIV Rate", "2014_HIV Rate", "2015_HIV Rate", "2016_HIV Rate", "2017_HIV Rate", "2018_HIV Rate", "2019_HIV Rate", "2020_HIV Rate", "2021_HIV Rate", "2022_HIV Rate", "2023_HIV Rate", "2024_HIV Rate", "2025_HIV Rate", "2026_HIV Rate"];

// Define the number of variable that you want to visaulize Comparision Line Chart. 
//var NumOfCLC = 0;
var NumOfCLC = 15;
// Define variables that you want to visualize at CLC (Comparision Line Chart).
//var InitialVariableCLC = ["2012_HIV Rate", "2013_HIV Rate", "2014_HIV Rate", "2015_HIV Rate", "2016_HIV Rate", "2017_HIV Rate", "2018_HIV Rate", "2019_HIV Rate", "2020_HIV Rate", "2021_HIV Rate", "2022_HIV Rate"]
//var InitialVariableCLC = [];
var InitialVariableCLC = ["2012_HIV Rate", "2013_HIV Rate", "2014_HIV Rate", "2015_HIV Rate", "2016_HIV Rate", "2017_HIV Rate", "2018_HIV Rate", "2019_HIV Rate", "2020_HIV Rate", "2021_HIV Rate", "2022_HIV Rate", "2023_HIV Rate", "2024_HIV Rate", "2025_HIV Rate", "2026_HIV Rate"];
var DefaultRegion_CLC = ["42101", "4013"];
var HighlightCLC = [["2021", "2026", "#fdff32"]];


// Define the number of variable that you want to visualize Multiple Synchronized Line Chart.
var NumOfMLC = 0;
//var NumOfMLC = 4;
// Define variables that you want to visualize at MLC (Multiple Synchronized Line Chart).
var InitialVariableMLC = []
//var InitialVariableMLC = ["HIV Rate", "Viral Load Test within 1 Month of Diagnosis (/100k pop)", "Rate of Illicit Drug Use", "Health Care Center (/100k pop)"];
// Define titles that you want to visualize at MLC (Multiple Synchronized Line Chart).
//var titlesOfMLC = ["HIV Rate", "Viral Load Test within 1 Month of Diagnosis (/100k pop)", "Rate of Illicit Drug Use", "Health Care Center (/100k pop)"];
var titlesOfMLC = [];
// Define beginning and ending of highlighted areas of MLC. You can do multiple times
// [["begin_X_value","end_X_value","color"], ["begin_X_value","end_X_value","color"]…] 
var DefaultRegion_MLC = "42101"; //Set highlighted ranges for x value
var HighlightMLC = [["2021", "2026", "#fdff32"]];


// Define no display variables of Top10 Bar cart
var Top10_NoDisplay = [ "HIV Test", "Illicit Drug Use Rate", "Knowledge", "Linkage to Care"];
//Define the geographic id or name to be display on the top-right corner of the map
//var NameDisplayed = "geoname";

// Define variables that you want to visualize at initial map views. For example, 
// enter five variables when the NumOfMaps is equal to 5.
//var InitialLayers = [];
var InitialLayers = ["2012_HIV Rate", "2026_HIV Rate"];

/*Define initial map center and zoom level below. Map Extent and Zoom level will be automatically adjusted when you do not define map center and zoom level. Double-slashes  in the front need to be deleted to make them effective*/
//var Initial_map_center = null;  
//var Initial_map_zoom_level = null;
var Initial_map_center = [38, -97];  
var Initial_map_zoom_level = 4;

// It shows the change in the number of polygons belonging to each class intervals in different 
// It appears only when the map extent and the class intervals of all maps are same.
// To make all maps have the same map extent and class intervals, 
// enable "Grouping All" or click "Sync" on one of maps
var Stacked_Chart = false;
var Correlogram = false;
var Scatter_Plot = false;
var Top10_Chart = false;
var Parallel_Coordinates_Plot = false;
var Comparision_Chart = false;
var Multiple_Line_Chart = false;

// The number of digit after the decial point.
var Num_Of_Decimal_Places = 2;                              // default = 1 

//Adjust the size of maps
var Map_width = "720px";
var Map_height  = "400px";                                  // min 300px

//Adjust the size of the stacked chart. Double-slashes in the front need to be deleted to make them effective
var Chart_width  = "350px";									// min 350px
var Chart_height = "350px";									// min 300px


