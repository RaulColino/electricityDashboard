import pandas as pd # To load dataframes from csv and work with them
import geopandas as gpd # To load dataframe from geojson file needed for the map.
import streamlit as st
import folium #For choropleth map
from streamlit_folium import folium_static # Streamlit component needed to use folium
import altair as alt # Stacked area chart

### Get executable directory to find the files required to run the application
# import sys, os
# exe_path = os.path.dirname(sys.executable)

### We need to pass the geojson file location to the parameter 'geo_data' of 'folium.Choropleth()' function
GEOJSON_FILE = "./world-countries-geojson.json"
DATASET_FILE = "./electricity_gdp_access_population_continent.csv"
COUNTRIES_FILE = "./countries.csv"

### Initial setup
#st.set_page_config(layout='wide', page_icon=':ambulance:')
st.set_page_config(
    layout="wide", # set_page_config() can only be called once per app, and must be called as the first Streamlit command in your script
    page_title="World electricity generation",
    page_icon='⚡️',
)
st.title("World Electricity Generation")
# st.markdown(
#     """
#     *Check out my cool data visualization dashboard*
#     """
# )

### Load dataset
df = pd.read_csv(DATASET_FILE)
### Load geojson file with geopandas
df_geojson = gpd.read_file(GEOJSON_FILE)

### Create country list
df_countries = pd.read_csv(COUNTRIES_FILE)
country_list = df_countries.columns.values.tolist()[1:]

# ---------------------------------------------------------------
# INPUT

def load_input():
    # Source selection
    choice = ["Hydro", "Solar", "Wind", "Other_renewables", "Oil", "Coal", "Gas", "Nuclear", "All sources combined"]
    choice_selected = st.selectbox(
        "Select energy source",
        choice
    )
    # Year selection
    year = st.slider(
        'Select year',
        min_value = 2009,
        max_value = 2019,
    )
    # Countries selection
    countries_selection = st.multiselect(
        label='Select countries to compare',
        options=country_list,
        default=country_list[45:55]
    )
    return choice_selected, year, countries_selection

# ---------------------------------------------------------------
# INPUT COUNTRY
def load_input_country():
    selected_country = st.selectbox(
     'Select a country to show energy source distribution',
     (country_list))
    return selected_country

# ---------------------------------------------------------------
# SCATTERPLOT

def loadScatterPlot(df, energy_src_selected, year_selected, countries_selection):
    df_scatterplot = df[df["Year"] == year_selected]
    df_scatterplot = df_scatterplot[df_scatterplot["Code"].isin(countries_selection)]
    scatter = alt.Chart(df_scatterplot).mark_circle(size=60).encode(
        alt.X(energy_src_selected, title="Electricity generated from {} energy (TWh)".format(energy_src_selected) ,scale=alt.Scale(zero=False)),
        alt.Y("GDP", scale=alt.Scale(zero=False, padding=1)),
        color="Entity",
        size="Population (historical estimates)",
        tooltip= [
            alt.Tooltip(field="Entity", title="Country", type="nominal"),
            alt.Tooltip(field="GDP", title="GDP", type="nominal"),
            alt.Tooltip(field="Population (historical estimates)", title="Population (historical estimates)", type="quantitative"),
            alt.Tooltip(field=energy_src_selected, title="Electricity generated from {} (TWh)".format(energy_src_selected), type="quantitative"),
        ],
    ).interactive(
    ).properties(
        height=500,
    )
    st.altair_chart(scatter, use_container_width=True)

# ---------------------------------------------------------------
# RANKING OF COUNTRIES (ELECTRICITY)

def load_ranking_elec(df, choice_selected, countries_selection, year_selected):
    df_ranking = df[df["Code"].isin(countries_selection)]
    df_ranking = df_ranking[df_ranking["Year"]==year_selected]
    ranking_elec = alt.Chart(df_ranking).mark_bar().encode(
        y = alt.X("Entity", title="Country", type="nominal", sort=alt.EncodingSortField(field=choice_selected, order='descending')),
        x = alt.Y(choice_selected, title="Electricity generated from {} (TWh)".format(choice_selected),type="quantitative"),
        tooltip= [
            alt.Tooltip(field="Entity", title="Country", type="nominal"),
            alt.Tooltip(field=choice_selected, title="Electricity generated from {} (TWh)".format(energy_src_selected), type="quantitative"),
        ],
    ).configure_mark(
        opacity=0.7,
    )
    st.altair_chart(ranking_elec, use_container_width=True)

# ---------------------------------------------------------------
# RANKING OF COUNTRIES (ELECTRICITY ACCESS)
def load_ranking_access(df, countries_selection, year_selected):
    df_ranking = df[df["Code"].isin(countries_selection)]
    df_ranking = df_ranking[df_ranking["Year"]==year_selected]
    ranking_acc = alt.Chart(df_ranking).mark_bar().encode(
        y = alt.X("Entity", title="Country", type="nominal", sort=alt.EncodingSortField(field="Access to electricity (% of population)", order='descending')),
        x = alt.Y("Access to electricity (% of population)", type="quantitative"),
        tooltip= [
            alt.Tooltip(field="Entity", title="Country", type="nominal"),
            alt.Tooltip(field="Access to electricity (% of population)" , title="access", type="quantitative"),
        ],
    ).configure_mark(
        opacity=0.7,
        color="#7D3C98"
    )
    st.altair_chart(ranking_acc, use_container_width=True)

# ---------------------------------------------------------------
# CHOROPLETH MAP

def load_map(df, df_geojson, choice_selected="GDP", year_selected=2015):
    # Custom code to make map with responsive
    make_map_responsive= """
    <style>
    [title~="st.iframe"] { width: 100%}
    </style>
    """
    st.markdown(make_map_responsive, unsafe_allow_html=True)

    ### Create custom data for the map 
    df_year_data = df[df["Year"] == year_selected]
    df_geojson = df_geojson[["id","geometry"]] #only select 'id' and 'geometry' columns
    # Finally join the geojson file with df
    df_map = df_geojson.merge(df_year_data, left_on="id", right_on="Code", how="outer") 
    df_map = df_map[~df_map["geometry"].isna()]
    #df_map
    
    # Base layer
    map = folium.Map(
        location=[90, 0],
        height=350,
        maxZoom=6,
        minZoom=1,
        zoom_control=True,
        zoom_start=1,
        max_bounds=True,
        tiles="Stamen",
        attr="Map tiles by Stamen Design, under by OpenStreetMap, under ODbL.",
        dragging=True,
    )

    # Add color layer
    folium.Choropleth(
        geo_data=GEOJSON_FILE,
        data=df_map,
        name="choropleth",
        columns=["Code", choice_selected],
        key_on="feature.id",
        fill_color="YlGn",
        nan_fill_color="White",
        fill_opacity=0.7,
        line_opacity=0.2,
        line_color='black',
        highlight=True,
        legend_name="Electricity generation from " + choice_selected + " (TWh)",
    ).add_to(map)

    # Add tooltip
    folium.features.GeoJson(
        data=df_map,
        style_function=lambda x: {
            'color':'transparent',
            'fillColor':'transparent',
            },
        popup=folium.features.GeoJsonPopup(
            fields=["Entity", choice_selected],
            ),
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Entity", choice_selected,],
            aliases=["Country :", "%s :"%(choice_selected),], 
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: #FFFFFF;
                border-radius: 10px;
                box-shadow: 8px;
            """,
            max_width=800,
            ),
        highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
    ).add_to(map)
    # return map with streamlit_folium function
    folium_static(map)

# ---------------------------------------------------------------
# STACKED AREA CHART

def load_stacked_area_chart(df, selected_country="ESP"):
    ### create custom data for the stacked area chart 
    df_stacked =  df[df["Code"] == selected_country]
    stacked = alt.Chart(df_stacked).transform_fold(
        ["Hydro", "Solar", "Wind", "Other_renewables", "Oil", "Coal", "Gas", "Nuclear"],
        as_ = ['EnergySources', 'Electricity (TWh)']
    ).mark_area().encode(
        alt.X(field='Year', type='temporal'),
        alt.Y(field='Electricity (TWh)', type='quantitative', stack='zero'),
        alt.Color('EnergySources:N')
    ).properties(width=500, height=300)

    st.altair_chart(stacked)

# ---------------------------------------------------------------
# FINAL LAYOUT

with st.container():
    col1a, col2a = st.columns([1, 2])
    with col1a:
        energy_src_selected, year_selected, countries_selection = load_input()
    with col2a:
        loadScatterPlot(df, energy_src_selected, year_selected, countries_selection)

with st.container():
    col1b, col2b = st.columns([2, 2])
    with col1b:
        load_ranking_elec(df, energy_src_selected, countries_selection, year_selected)
    with col2b:
        load_ranking_access(df, countries_selection, year_selected)

with st.container():
    col1c, col2c = st.columns([2, 1])
    with col1c:
        load_map(df, df_geojson, energy_src_selected, year_selected)
    with col2c:
        selected_country = load_input_country()
        load_stacked_area_chart(df, selected_country)





