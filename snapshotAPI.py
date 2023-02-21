#!/usr/bin/env python
# coding: utf-8

# In[1]:

import pandas as pd
import requests
import json
import datetime
import time


class snapshotAPI:
    def __init__(self):
        self.snapshotURI = 'https://hub.snapshot.org/graphql'
        self.statusCode = 200
        
    def runQuery(self, query):
        request = requests.post( self.snapshotURI, json={'query': query})
        if request.status_code == self.statusCode:
            return request.json()
        else:
            raise Exception(f"Unexpected status code returned: {request.status_code}")
            
    
    def getProposal(self, proposalID):
        query = f"""query {{
          proposals (
            where: {{
              id: "{proposalID}"
            }},
          ) {{
            choices
            start
            end
            snapshot
            scores
            scores_by_strategy
            scores_total
            scores_updated
            author
          }}
        }}
        """
        result = self.runQuery(query)
        return result
        
    
    
    def getProposalDataFrame(self, proposalID):
        
        #Get the Data
        data = self.getProposal(proposalID)
        
        #Sort data to Data Frame
        headers = []
        dataHeader = list(data['data'].keys())[0]
        #Get data Headers
        for key ,value in data['data'][dataHeader][0].items():
            headers.append(key)

        #Set up basic information
        proposalDF = pd.DataFrame(columns =headers )
        for head in headers:
            if not head in ['choices', 'scores', 'scores_by_strategy']:
                proposalDF.loc[0,head] = data['data'][dataHeader][0][head]

        #Choices
        choices = []
        for choice in (data['data'][dataHeader][0]['choices']):
            choices.append(choice)

        #Results
        scores = []
        for score in (data['data'][dataHeader][0]['scores']):
            scores.append(score)

        #Join on dataframe
        for i in range(len(choices)):
            d = {choices[i]: [scores[i]]}
            datainput = pd.DataFrame(data=d)
            proposalDF = pd.concat([proposalDF, datainput], axis=1)

        return proposalDF
    
    
    def getVotingPower(self,snapshotSpace,proposalID,voterAddress):
        query= f"""query {{
              vp (
                voter: "{voterAddress}"
                space: "{snapshotSpace}"
                proposal: "{proposalID}"
              ) {{
                vp
                vp_by_strategy
                vp_state
              }} 
            }}"""
        
        result = self.runQuery(query)
        return result
        

    
        
    def getVotes(self, proposalID, skip=0):
        time.sleep(2)
        query = f"""query {{
          votes (
            first: 1000
            skip: {skip}
            where: {{
              proposal: "{proposalID}"
            }}
            orderBy: "created",
            orderDirection: desc
          ) {{
            voter
            vp
            created
            proposal {{
              id
            }}
            choice
          }}
        }}"""
        
        result = self.runQuery(query)
        return result
    
    
    def getVotingChoice(self, proposalID):
        query = f"""query {{
          proposals (
            where: {{
              id: "{proposalID}"
            }},
          ) {{
            choices
          }}
        }}
        """
        
        result = self.runQuery(query)
        return result['data']['proposals'][0]['choices']
    
    def getVotingTimeVolume(self, proposalID):
        query = f"""query {{
              votes (
                first: 3000
                skip: 0
                where: {{
                  proposal: "{proposalID}"
                }}
                orderBy: "created",
                orderDirection: desc
              ) {{
                vp
                created
              }}
          }}
        """
        result = self.runQuery(query)
        return result['data']['votes']
        
    def getTimeVolDF(self, proposalID):
        data = self.getVotingTimeVolume(proposalID)
        
        volTimeDF = pd.DataFrame(data)
        
        for i in range(len(volTimeDF)):
            volTimeDF.loc[i,'created'] = (datetime.datetime.fromtimestamp(volTimeDF.loc[i,'created'], datetime.timezone.utc))
        
        return volTimeDF


    def getAllProposals(self,spaceName):
        query = f"""query {{
          proposals (
            first: 1000,
            skip: 0,
            where: {{
              space_in: ["{spaceName}"],
              state: "closed"
            }},
            orderBy: "created",
            orderDirection: desc
          ) {{
            id
            title
            start
            end
            snapshot
            state
            choices
            scores
            scores_updated
          }}
        }}
        """
        #scores_total
        #choices
        
        result = self.runQuery(query)
        return result['data']['proposals']
        
    def getAllProposalDF(self,spaceName):
        data = self.getAllProposals(spaceName)
        
        proposalDF = pd.DataFrame(data=data)
        return proposalDF
            
                   
        
    
    def getVotesDF(self, proposalID):
        
   
        data = self.getVotes(proposalID)
        
        headers = []
        dataHeader = list(data['data'].keys())[0]
        #Get data Headers
        for key ,value in data['data'][dataHeader][0].items():
            headers.append(key)

        #Set up basic information
        voteDF = pd.DataFrame(columns =headers )

        #Set up basic information
        for head in headers:
            if not head in ['choice', 'proposal']:
                for i in range(len(data['data'][dataHeader])):
                    voteDF.loc[i,head] = data['data'][dataHeader][i][head]    

        
        #Concant choices to dataframe
        choices = self.getVotingChoice(proposalID)
        choiceNamesDf = pd.DataFrame(columns = choices )
        voteDF = pd.concat([voteDF, choiceNamesDf], axis=1)
    
        for i in range(len(voteDF)):
            for j in range(len(data['data']['votes'][i]['choice'].keys())):
                totalDispersed = (sum(list(data['data']['votes'][i]['choice'].values())))
                voteDF.loc[i][(len(headers) -1) + int(list(data['data']['votes'][i]['choice'].keys())[j])] =  ((list(data['data']['votes'][i]['choice'].values())[j]) / totalDispersed) * data['data']['votes'][i]['vp']
        
        
        
        return voteDF

