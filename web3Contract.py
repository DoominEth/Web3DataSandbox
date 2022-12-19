#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Etherscan
from etherscan import Etherscan
#Web 3

from web3 import Web3, EthereumTesterProvider
class web3Contract:
    def __init__(self, ENDPOINT, ETHERSCAN_API):
        self.web3 =  Web3(Web3.HTTPProvider(ENDPOINT))
        self.etherscan = Etherscan(ETHERSCAN_API)
    
    def createContract(self, address):
        contractAddress =  Web3.toChecksumAddress(address)
        abi = self.etherscan.get_contract_abi(address)
        contractInstance = self.web3.eth.contract(address=contractAddress, abi=abi)
        return contractInstance
        

