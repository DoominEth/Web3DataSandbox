from web3 import Web3, EthereumTesterProvider
from etherscan import Etherscan
import pandas as pd
import numpy as np
from datetime import datetime
import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from scipy.stats import pearsonr


class GaugeMapping:
    def __init__(self, web3, etherscan, snapshot):
        self.web3 = web3
        self.etherscan = etherscan
        self.snapshot = snapshot
        self.allMappingData =  pd.read_excel('OTHER_FINAL_DF.xlsx')
        self.allMappingData['DateTime'] = self.allMappingData['DateTime'].dt.strftime('%Y-%m-%d')
    
    
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
        #gMap = self.buildAllGaugeInfo(gaugeAddress)
        gMap = pd.read_excel('gaugeMapTom.xlsx')
        snapshotData = self.allGaugeData(snapshotSpace)
        oldGMap = self.mapOldData(snapshotData, gMap,oldIndex)
        oldGMap = self.oldGaugeDataFill(snapshotData,oldGMap, oldIndex)
        oldGMap = self.oldGaugeCrossChain(oldGMap)
        oldGMap = self.UnixTimeToTimeDate(oldGMap)
        oldGMap = self.bribePerProposal(oldGMap, oldBribeData)
        totalBribes = self.totalBribes(oldGMap)
        oldGMap = self.addPercentages(oldGMap, totalBribes)
        return oldGMap
    
    
    def mapNewData(self, snapshot, gaugeMap,newIndex):
        cols = ['Name','SnapshotIndex','GaugeControllerIndex','Votes']
        mappingDF = pd.DataFrame(columns = cols)
        bIndex = 0
                
        for i in range(len(snapshot)):
            #Where Curve changed his
            if snapshot.loc[i]['id'] == "bafkreiepapq2rgoh4udx273ygz5lbgvg6ysnwva6kvz2rinj26lat7ilsm":
                bIndex = i
                scores = snapshot.loc[i, 'scores']
                choice = snapshot.loc[i, 'choices']
                for j in range(len(scores)):
                    word = choice[j]
                    mappingDF.loc[j,'Name'] = word
                    mappingDF.loc[j,'SnapshotIndex'] = j 
                    for k in range(len(gaugeMap)):
                        try:
                            poolAddress = gaugeMap.loc[k,'Pool']
                            gaugeName = (poolAddress[:6] +  '…'+ poolAddress[-4:])
                            if gaugeName.lower() in word.lower():
                                mappingDF.loc[j,'GaugeControllerIndex'] = k
                                mappingDF.loc[j,'Votes'] = scores[j]
                                #print(str(j) + ':')

                        except:
                                mappingDF.loc[j,'SnapshotIndex'] = j 
                                mappingDF.loc[j,'Votes'] = scores[j]
                                #print('ERROR')
                                pass
        return mappingDF, bIndex
    
    
    def newGaugeDataFill(self,newSnapshotData, mapData, gaugeControllerData, index):
        cols = ['Name','SnapshotIndex','GaugeControllerIndex','Votes', 'UnixTime']
        newDataFrame = pd.DataFrame(columns=cols)
        currentIndex = 0

        for i in range(0,index):
            scores = newSnapshotData.loc[i, 'scores']
            choice = newSnapshotData.loc[i, 'choices']
            endUnixTime = newSnapshotData.loc[i,'end']

            for j in range(len(scores)):       
                newDataFrame.loc[currentIndex,'Votes'] = scores[j]
                newDataFrame.loc[currentIndex,'SnapshotIndex'] = j
                word = choice[j]


                for k in range(len(mapData)):
                    mapName = mapData.loc[k, 'Name']
                    newDataFrame.loc[currentIndex,'Name'] = word
                    #newDataFrame.loc[currentIndex,'SnapshotIndex'] = j
                    newDataFrame.loc[currentIndex,'UnixTime'] = endUnixTime

                    try:
                        if word.lower()[:-1] in mapName.lower():
                            newDataFrame.loc[currentIndex,'GaugeControllerIndex'] = mapData.loc[k,'GaugeControllerIndex']
                            #newDataFrame.loc[currentIndex,'Votes'] = scores[j]
                            break
                        if(k ==len(mapData) - 1):
                            for l in range(len(gaugeControllerData)):                            
                                try:
                                    if word.split()[1][1:-2].lower() ==gaugeControllerData.loc[l,'Pool'][:6].lower():
                                        #print('New Address found (Non Beacon)')
                                        newDataFrame.loc[currentIndex,'GaugeControllerIndex'] = l
                                        #newDataFrame.loc[currentIndex,'Votes'] = scores[j]
                                        #print(f'Index:{currentIndex}')
                                except:
                                    continue


                    except:                    
                        pass


                currentIndex += 1

        return newDataFrame
    
    
    def newOtherChainData(self, mapData):
        ftm = 1000
        poly = 999
        arbi = 998
        ava = 997
        op = 996
        xdai = 995
        veFunder = 994

        for i in range(len(mapData)):
            poolName = mapData['Name'][i]
            if poolName[:4] == 'ftm-':
                mapData['GaugeControllerIndex'][i] = ftm
            elif poolName[:5] == 'poly-':
                mapData['GaugeControllerIndex'][i] = poly
            elif poolName[:5] == 'arbi-':
                mapData['GaugeControllerIndex'][i] = arbi
            elif poolName[:4] == 'ava-':
                mapData['GaugeControllerIndex'][i] = ava
            elif poolName[:3] == 'op-':
                mapData['GaugeControllerIndex'][i] = op
            elif poolName[:5] == 'xdai-':
                mapData['GaugeControllerIndex'][i] = xdai
            elif poolName[:9] == 'VeFunder-':
                mapData['GaugeControllerIndex'][i] = veFunder
            else:
                pass
        return mapData

    
    def buildNewGaugeMapping(self, gaugeAddress, snapshotSpace, newIndex, newBribeData):
        #gMap = self.buildAllGaugeInfo(gaugeAddress)
        gMap = pd.read_excel('gaugeMapTom.xlsx')
        snapshotData = self.allGaugeData(snapshotSpace)
        newGMap, index = self.mapNewData(snapshotData, gMap,newIndex)
        newGMap = self.newGaugeDataFill(snapshotData, newGMap,gMap,index )
        newGMap = self.newOtherChainData(newGMap) 
        newGMap = self.UnixTimeToTimeDate(newGMap)
        newGMap = self.bribePerProposal(newGMap, newBribeData)
        newTotalBribes = self.totalBribes(newGMap)
        newGMap = self.addPercentages(newGMap, newTotalBribes)
        return newGMap
    
    
    def differenceBetweenBribeAndVote(self,data):
        for i in range(len(data)):
            #if data.loc[i, 'vote%'] == 0 and  data.loc[i, 'bribe%'] == 0:
            if data.loc[i, 'bribe%'] == 0:   
                data.loc[i,'differenceFromBribe%'] = float('NaN')

            else:
                data.loc[i,'differenceFromBribe%'] = data.loc[i, 'vote%'] - data.loc[i, 'bribe%']

        return data
    
    
    
    def drawHeatMap(self, dataframe):        
        plt.figure(figsize=(30,10))
        ax = sns.heatmap(data=dataframe, annot=False)
        plt.tight_layout()
        plt.show()
    
    
    
    def drawHeatMapDiffernceBetweenVotesBribes(self, dataFrame):
        dataFrame = self.differenceBetweenBribeAndVote(dataFrame)

        newPivot = dataFrame.pivot_table(index='DateTime', columns="GaugeControllerIndex", values='differenceFromBribe%')
        bribe_sum = dataFrame.groupby("GaugeControllerIndex")["bribeValueUSD"].sum()

        # Sort the bribe_sum in descending order
        bribe_sum = bribe_sum.sort_values(ascending=False)

        # Reorder the columns of the pivot table
        newPivot = newPivot.reindex(columns=bribe_sum.index)

        newPivot = newPivot.dropna(axis=1, how='all')

        # Sort the rows by the index (dates) in ascending order
        newPivot = newPivot.sort_index()

        # Plot the heatmap
        self.drawHeatMap(newPivot)

        
        
    def drawVoteHeatMap(self,dataFrame):
        newPivot = dataFrame.pivot_table(index='DateTime', columns="GaugeControllerIndex", values='vote%')
        bribe_sum = dataFrame.groupby("GaugeControllerIndex")["bribeValueUSD"].sum()

        # Sort the bribe_sum in descending order
        bribe_sum = bribe_sum.sort_values(ascending=False)

        # Reorder the columns of the pivot table
        newPivot = newPivot.reindex(columns=bribe_sum.index)

        newPivot = newPivot.dropna(axis=1, how='all')
        
        # Plot the heatmap
        self.drawHeatMap(newPivot)

        

        
    def drawBribeHeatMap(self,dataFrame):
        newPivot = dataFrame.pivot_table(index='DateTime', columns="GaugeControllerIndex", values='bribe%')
        bribe_sum = dataFrame.groupby("GaugeControllerIndex")["bribeValueUSD"].sum()

        # Sort the bribe_sum in descending order
        bribe_sum = bribe_sum.sort_values(ascending=False)

        # Reorder the columns of the pivot table
        newPivot = newPivot.reindex(columns=bribe_sum.index)

        newPivot = newPivot.dropna(axis=1, how='all')

        # Plot the heatmap
        self.drawHeatMap(newPivot)

        
        
    def getUniqueTimes(self, df):
        unique_values = df['UnixTime'].unique()
        return unique_values
        
    def drawLinearRegression(self, time, df, withNonBribed):
        if withNonBribed:
            df_filtered = df[(df['UnixTime'] == time) & (df['bribe%'] > 0)]
        else:
            df_filtered = df[(df['UnixTime'] == time) ]

        x = df_filtered['bribe%'].values
        y = df_filtered['vote%'].values

        model = LinearRegression()
        model.fit(x[:, np.newaxis], y[:, np.newaxis])

        #coefficient = model.coef_[0][0]
        
        #x = df['bribe%'].values
        #y = df['vote%'].values
        correlation_coefficient = np.corrcoef(x, y)[0, 1]
        
        
        date = datetime.fromtimestamp(time).strftime('%Y-%m-%d')

        x_new = np.linspace(0, 20, 30, 40,50)
        y_new = np.linspace(0, 20, 30, 40,50)
        plt.figure(figsize=(10, 10))
        ax = plt.axes()
        ax.scatter(x, y)
        ax.plot(40,40)
        ax.set_xlabel('Bribe %')
        ax.set_ylabel('Vote %')
        ax.axis('tight')
        ax.set_title(f'Correlation Coefficient at Time {date}: {correlation_coefficient:.2f}')
        plt.show()
    
    
    def drawAllCorolationOneChart(self, df, withNonBribed):
        
        if withNonBribed:
            df_filtered = df[df['bribe%'] > 0]
        else:
            df_filtered = df

        
        x = df_filtered['bribe%'].values
        y = df_filtered['vote%'].values
        
        correlation_coefficient = np.corrcoef(x, y)[0, 1]
        
        model = LinearRegression()
        model.fit(x[:, np.newaxis], y[:, np.newaxis])

        #coefficient = model.coef_[0][0]
                

        x_new = np.linspace(0, 20, 30, 40,50)
        y_new = np.linspace(0, 20, 30, 40,50)
        plt.figure(figsize=(10, 10))
        ax = plt.axes()
        ax.scatter(x, y)
        ax.plot(40,40)
        ax.set_xlabel('Bribe %')
        ax.set_ylabel('Vote %')
        ax.axis('tight')
        ax.set_title(f'Overall Correlation Coefficient - {correlation_coefficient:.2f}')
        plt.show()
    
    def drawAllGaugeProposalCorolation(self, df, withNonBribed):
        uniquePropTimes = self.getUniqueTimes(df)
        
        for time in uniquePropTimes:
            self.drawLinearRegression(time,df,withNonBribed )
            
            
           