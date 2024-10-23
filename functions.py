
import requests
import pandas as pd
import json
import streamlit as st
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
from st_link_analysis.component.icons import SUPPORTED_ICONS

def return_entities(url, token):
        
    url = f"{url}/api/states"

    payload = json.dumps({})
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
    }

    response = json.loads(requests.request("GET", url, headers=headers, data=payload).text)
    dfEntidades = pd.DataFrame(response)

    dfEntidades["entity_type"] = dfEntidades["entity_id"].apply(lambda x: x.split(".")[0])

    dfEntidades = dfEntidades[['entity_id','entity_type','state','last_changed']]

    return dfEntidades
