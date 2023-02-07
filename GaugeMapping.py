from web3 import Web3, EthereumTesterProvider
from etherscan import Etherscan
import pandas as pd
import numpy as np
from datetime import datetime
import json


class GaugeMapping:
    def __init__(self, web3, etherscan, snapshot):
        self.web3 = web3
        self.etherscan = etherscan
        self.snapshot = snapshot
    
    
    def buildAllGaugeInfo(self, gaugeAddress):
    #mapping DF
        gaugeMappingDF = pd.DataFrame()

        #Missing details counter
        counter = 0

        #Gauge Controller Address
        gaugeControllerAddress = Web3.toChecksumAddress(gaugeAddress )
        gaugeControllerAddressABI = self.etherscan.get_contract_abi(gaugeControllerAddress) 
        gaugeControllerAddressContract = self.web3.eth.contract(address=gaugeControllerAddress, abi=gaugeControllerAddressABI)

        #Registry Address
        regAddress = Web3.toChecksumAddress('0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC')
        regAddressABI =  self.etherscan.get_contract_abi(regAddress)
        regAddressContract = self.web3.eth.contract(address=regAddress, abi=regAddressABI)

        for i in range(gaugeControllerAddressContract.functions.n_gauges().call()):
            gaugeAddr = Web3.toChecksumAddress(gaugeControllerAddressContract.functions.gauges(i).call())
            try:
                #gaugeAddr = Web3.toChecksumAddress(gaugeControllerAddressContract.functions.gauges(i).call())
                gaugeMappingDF.loc[i, 'Gauge_Address'] = gaugeAddr

                currentGaugeABI = self.etherscan.get_contract_abi(gaugeAddr) 
                currentGaugeContract = self.web3.eth.contract(address=gaugeAddr, abi=currentGaugeABI)

                try:
                    lpTokenAddr = currentGaugeContract.functions.lp_token().call()
                    gaugeMappingDF.loc[i, 'LP_Token'] = lpTokenAddr

                    pool = Web3.toChecksumAddress(regAddressContract.functions.get_pool_from_lp_token(lpTokenAddr).call())
                    gaugeMappingDF.loc[i, 'Pool'] = pool

                    gaugeMappingDF.loc[i, 'Name'] = regAddressContract.functions.get_pool_name(pool).call()

                except:
                    #print('entered')
                    lpTokenAddr = currentGaugeContract.functions.coins(1).call()
                    print(lpTokenAddr)
                    pool = Web3.toChecksumAddress(regAddressContract.functions.get_pool_from_lp_token(lpTokenAddr).call())
                    print(pool)
                    if pool != Web3.toChecksumAddress('0x0000000000000000000000000000000000000000'):
                        #print(f'Added at index {i}')
                        gaugeMappingDF.loc[i, 'LP_Token'] = lpTokenAddr
                        gaugeMappingDF.loc[i, 'Pool'] = pool
                        gaugeMappingDF.loc[i, 'Name'] = regAddressContract.functions.get_pool_name(pool).call()

            except:            
                #print(f'{counter}. missing information for Gauge {i}: {gaugeAddr}')
                counter += 1

        return gaugeMappingDF
    
    def getAllSnapshotProposals(self, snapshotSpace):
        allProposals = self.snapshot.getAllProposals(snapshotSpace)
        dataDF = pd.DataFrame(allProposals)
        return dataDF
        
    def getGaugeOnly(self,allProps):
        gaugeIndices = []
        for i in range(len(allProps)):
            if allProps.loc[i]['title'].split()[0] == 'Gauge':
                gaugeIndices.append(i)
            gaugeDataIndices = []
            for index in gaugeIndices:
                gaugeDataIndices.append(allProps.loc[index])

            gaugeData = pd.DataFrame(gaugeDataIndices)
            gaugeData = gaugeData.reset_index(drop = True)

        return gaugeData
    
    def allGaugeData(self,snapshotSpace):
        allProposals = self.getAllSnapshotProposals(snapshotSpace)
        gaugeSnapshotData = self.getGaugeOnly(allProposals)
        return gaugeSnapshotData
        
    def mapOldData(self, snapShotData, gaugeData, indexOfOldData):
        cols = ['Name','SnapshotIndex','GaugeControllerIndex','Votes']
        oldDF = pd.DataFrame(columns = cols)
        
        for i in range(len(snapShotData)):
            if i == indexOfOldData:
                for j in range(len(snapShotData.loc[i, 'choices'])):
                    oldDF.loc[j, 'Name'] = snapShotData.loc[i, 'choices'][j]
                    oldDF.loc[j, 'Votes'] = snapShotData.loc[i, 'scores'][j]
                    for k in range(len(gaugeData)):
                        if oldDF.loc[j, 'Name'] == gaugeData['Name'][k]:
                            oldDF.loc[j, 'GaugeControllerIndex'] = k

        return oldDF
    
    
    def oldGaugeDataFill(self, oldSnapshotData, mapData, indexOfOldData):
        cols = ['Name','SnapshotIndex','GaugeControllerIndex','Votes', 'UnixTime']
        newDataFrame = pd.DataFrame(columns=cols)
        currentIndex = 0
    
        for i in range(indexOfOldData,len(oldSnapshotData)):
            scores = oldSnapshotData.loc[i, 'scores']
            choice = oldSnapshotData.loc[i, 'choices']
            endUnixTime = oldSnapshotData.loc[i,'end']

            for j in range(len(scores)):       
                newDataFrame.loc[currentIndex,'Votes'] = scores[j]
                newDataFrame.loc[currentIndex,'SnapshotIndex'] = j
                word = choice[j]

                for k in range(len(mapData)):
                    Name = mapData.loc[k, 'Name']
                    newDataFrame.loc[currentIndex,'Name'] = word
                    #newDataFrame.loc[currentIndex,'SnapshotIndex'] = j
                    newDataFrame.loc[currentIndex,'UnixTime'] = endUnixTime

                    if newDataFrame.loc[currentIndex,'Name'] == Name:
                        newDataFrame.loc[currentIndex,'GaugeControllerIndex'] = mapData.loc[k, 'GaugeControllerIndex']                
                        break
                currentIndex += 1

        return newDataFrame
    
    
    def oldGaugeCrossChain(self, data):
        #This function assigns a different number to each gauge that is not on the Ethereum blockchain
        ftm = 1000
        poly = 999
        arbi = 998
        ava = 997
        op = 996
        xdai = 995
        veFunder = 994
        Harmony = 993
    
        for i in range(len(data)):
            if(len(data.loc[i,'Name']) >7):
                if data.loc[i,'Name'][:7] == 'fantom-':
                    data.loc[i, 'GaugeControllerIndex'] = ftm
                    continue
                elif data.loc[i,'Name'][:7] == 'polygon':
                    data.loc[i, 'GaugeControllerIndex'] = poly
                    continue
                elif data.loc[i, 'Name'][:7] == 'arbitru':
                    data.loc[i, 'GaugeControllerIndex'] = poly
                    continue
                elif data.loc[i, 'Name'][:7] == 'optimis':
                    data.loc[i, 'GaugeControllerIndex'] = op
                    continue
                elif data.loc[i, 'Name'][:5] == 'xdai-':
                    data.loc[i, 'GaugeControllerIndex'] = xdai
                    continue
                elif data.loc[i, 'Name'][:6] =='VeFunde':
                    data.loc[i, 'GaugeControllerIndex'] = veFunder
                    continue
                elif data.loc[i, 'Name'][:7] == 'avalanc':
                    data.loc[i, 'GaugeControllerIndex'] = ava
                    continue
        return data
    
    def UnixTimeToTimeDate(self,data):
        for i in range(len(data)):
            time = datetime.fromtimestamp(data['UnixTime'][i], tz=None)
            time = datetime(time.year,time.month,time.day)
            data.loc[i, 'DateTime'] = time.date()
        return data
    
    def bribePerProposal(self,mapData, bribeData):
        mapData['bribeValueUSD'] = 0
        for i in range(len(bribeData)):
            for j in range(len(mapData)):
                if  datetime.strptime(bribeData['deadline'][i][:10],  "%Y-%m-%d").date() == mapData.loc[j, 'DateTime']:
                    if bribeData.loc[i,'_choiceIndex'] == mapData.loc[j, 'SnapshotIndex']:
                        if mapData.loc[j,'bribeValueUSD'] > 0:
                            mapData.loc[j,'bribeValueUSD'] = mapData.loc[j,'bribeValueUSD'] + bribeData.loc[i,'amount_usd']     
                        else:
                             mapData.loc[j,'bribeValueUSD'] = bribeData.loc[i,'amount_usd']

        return mapData
    
    def totalBribes(self, voteBribeData):
        allTimes = voteBribeData['UnixTime'].drop_duplicates()
        #allTimes = voteBribeData['deadline'].drop_duplicates()
        totalBribeDF= pd.DataFrame(data=allTimes)
        totalBribeDF = totalBribeDF.reset_index(drop=True)
        for i in range(len(totalBribeDF)):
            totalBribeDF.loc[i,'totalBribes'] = voteBribeData.loc[voteBribeData['UnixTime'] ==  totalBribeDF.loc[i,'UnixTime'], 'bribeValueUSD'].sum()
            totalBribeDF.loc[i,'totalVotes'] = voteBribeData.loc[voteBribeData['UnixTime'] ==  totalBribeDF.loc[i,'UnixTime'], 'Votes'].sum()
        return totalBribeDF
        
    
    def addPercentages(self, mappingData, totalBribeDF):
        for i in range(len(mappingData)):
            for j in range(len(totalBribeDF)):
                if mappingData.loc[i, 'UnixTime'] == totalBribeDF.loc[j,'UnixTime']:
                    mappingData.loc[i, 'totalBribes'] =  totalBribeDF.loc[j,'totalBribes']
                    mappingData.loc[i, 'totalVotes'] =  totalBribeDF.loc[j,'totalVotes']

        for i in range(len(mappingData)):
            mappingData.loc[i, 'bribe%'] = (mappingData.loc[i, 'bribeValueUSD'] / mappingData.loc[i, 'totalBribes']) * 100
            mappingData.loc[i, 'vote%'] = (mappingData.loc[i, 'Votes'] / mappingData.loc[i, 'totalVotes']) * 100    

        return mappingData    
    
    def buildOldGaugeMapping(self, gaugeAddress, snapshotSpace, oldIndex, oldBribeData):
        gMap = self.buildAllGaugeInfo(gaugeAddress)
        snapshotData = self.allGaugeData(snapshotSpace)
        oldGMap = self.mapOldData(snapshotData, gMap,oldIndex)
        oldGMap = self.oldGaugeDataFill(snapshotData,oldGMap, oldIndex)
        oldGMap = self.oldGaugeCrossChain(oldGMap)
        oldGMap = self.UnixTimeToTimeDate(oldGMap)
        oldGMap = self.bribePerProposal(oldGMap, oldBribeData)
        totalBribes = self.totalBribes(oldGMap)
        oldGMap = self.addPercentages(oldGMap, totalBribes)
        return oldGMap