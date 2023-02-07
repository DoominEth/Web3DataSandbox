from web3 import Web3, EthereumTesterProvider
from etherscan import Etherscan
import json


class Node:
    def __init__(self, name, value, address, children=[]):
        self.name = name
        self.value = value
        self.children = children
        self.searched = False
        self.address = Web3.toChecksumAddress(address)
        

class NodeOperations:
    def __init__(self, web3, etherscan):
        self.web3 = web3
        self.etherscan = etherscan
        
    def print_tree(self, node, level=0):
        print('    ' * level + node.name + ": \t" + node.address)
        for child in node.children:
            self.print_tree(child, level+1)
    
    def depth_first_search(self, node, depth, current_depth=0, nodeIterator=0):
        if current_depth >= depth: #Escape after depth reached or exceeded
            return
        if node.searched == True:
            return

        availibleABI = True

        #Handler for non verified smart contracts on etherscan
        try:
            contractABI = self.etherscan.get_contract_abi(node.address) #Use Etherscan API to get the contracts ABI
        except:
            print('Problem with the ABI')
            availibleABI = False #unavailible ABI (contract code not verified)

        if availibleABI: #If contract's ABI is verified
            contractInstance = self.web3.eth.contract(address=node.address, abi=contractABI) #Use web3 Library to create an instantiation of the contract
            contractABI = json.loads(contractABI) #convert ABI to json format

            for i in range(len(contractABI)): #Examine all functions/methods/variables in the ABI
                try:
                    if contractABI[i]['outputs'][0]['type'] == 'address': #Searching exclusively for addresses on the contract
                        if len(contractABI[i]['inputs']) == 0:  #Check function call does not require input
                            childAddress = eval("contractInstance."+"functions."+contractABI[i]['name']+"()"+".call()") #RPC call to the contract, return the 20byte address
                            child = Node(contractABI[i]['name'], nodeIterator, childAddress, []) #create node
                            node.children.append(child) #Append child node
                            #nodeIterator += 1 
                            #print(f'Searching node...')
                        elif len(contractABI[i]['inputs']) == 1 and contractABI[i]['inputs'][0]['type'] == 'uint256': #This is an array of addresses:
                            print('Searching Array Node...')
                            try: 
                                for j in range(0,10):
                                    #print(j)
                                    childAddress = eval("contractInstance."+"functions."+contractABI[i]['name']+"("+str(j)+ ")"+".call()") #RPC call to the contract, return the 20byte address
                                    child = Node(contractABI[i]['name'], nodeIterator, childAddress, []) #create node
                                    node.children.append(child) #Append child node
                                    nodeIterator += 1 
                                    #print(f'Searching node...') #NOTE: Might need to put a check in for 0x0000... etc address.
                            except:
                                break
                        else:
                            pass
                except:
                    pass

            for child in node.children:
                child.name
                self.depth_first_search(child, depth, current_depth+1, nodeIterator)

            node.searched = True
        else: 
            print(node.address)
            node.name = 'NO ABI AVAILIBLE'
            node.searched = True
            pass