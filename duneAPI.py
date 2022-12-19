#!/usr/bin/env python
# coding: utf-8

# In[1]:
import pandas as pd
from duneanalytics import DuneAnalytics

class Dune_API:
    def __init__(self, email, password):
        self.email = email
        self.password = password

        
    def login(self):
        global dune
        dune = DuneAnalytics(self.email, self.password)
        dune.login()
        dune.fetch_auth_token()
    
    def getQueryDataByID(self,queryID):
        result_id = dune.query_result_id_v3(query_id=queryID)
        return dune.get_execution_result(result_id)
    
    def setUpDataFrame(self, data):
        data['data']['get_execution']['execution_succeeded']['columns']
        global duneDF
        cols =  data['data']['get_execution']['execution_succeeded']['columns']
        duneDF =pd.DataFrame(columns=cols)
        
    def fillDF(self, data):
        #data
        #cols = data['data']['get_execution']['execution_succeeded']['columns']
        #duneDF = pd.DataFrame(columns=cols)
        for i in range(0, len(data['data']['get_execution']['execution_succeeded']['columns'])):
                key = data['data']['get_execution']['execution_succeeded']['columns'][i]
                for j in range(0, len( data['data']['get_execution']['execution_succeeded']['data'])):
                    duneDF.loc[j, key] = data['data']['get_execution']['execution_succeeded']['data'][j][key]
        
                        
        
    def is_date(self,data):
        for i in range(len (duneDF.columns)):
            try:
                format_yyyymmdd = "%Y-%m-%d"
                datetime.datetime.strptime((duneDF.loc[0, duneDF.columns[i]])[:10],format_yyyymmdd)
                duneDF[duneDF.columns[i]]=  pd.to_datetime(duneDF[duneDF.columns[i]])
            except:
                pass
            
    def is_number(self):
        for i in range(len (duneDF.columns)):
            if (isinstance(duneDF[duneDF.columns[i]][0], (int, float))):
                duneDF[duneDF.columns[i]] =  pd.to_numeric(  duneDF[duneDF.columns[i]])
                
        
    
    def create_DF(self, queryID):
        self.login()
        data = self.getQueryDataByID(queryID)
        
        self.setUpDataFrame(data)
        self.fillDF(data)
        self.is_date(data)
        self.is_number()
        return duneDF

