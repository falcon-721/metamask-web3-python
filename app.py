from flask import Flask
from flask import *
import requests
from flask_cors import CORS
from OpenSea import getAPIResponse
from web3 import Web3, HTTPProvider
app = Flask(__name__)
CORS(app)

X_API_KEY = 'Jc5G75Rm2rWaGXmxMO3P8xQL9aJmZo7c1sZzvSluZ6TgV3Q3165T6RPEp0FNYHLy'
chains = ['eth','0x1','goerli','0x5','sepolia','0xaa36a7','polygon','0x89','mumbai','0x13881','bsc','0x38','bsc testnet','0x61','avalanche','0xa86a','avalanche testnet','0xa869','fantom','0xfa','cronos','0x19','cronos testnet','0x152']
alchemy_url_ethereum = "https://eth-mainnet.g.alchemy.com/v2/yd9Mtqsc1LIkfQi6fjBlGjAe93MWHiE-"

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        data = json.loads(request.data)
        session["address"] = data['address']
        return 'connected wallet successfully'
    return 'Welcome to login'
 
@app.route("/logout")
def logout():
    session["address"] = None
    return 'disconnected wallet'

@app.route("/")
def home():
    if not session.get("address"):
        return 'Please connect wallet'
    return "Hello, Flask!"

@app.route('/getChainInfo',methods = ['GET','POST'])
def chain_info():
    result_json = []
    result_data = []

    if not session.get("address"):
            return 'please connect wallet'
    
    if request.method == 'POST':
        data = json.loads(request.data)
        net = data['net']   # ethereum or solana
        chain = data['chain']   # eth, polygon, bsc
        address = data['address']
        balance_kind = data['balance_kind']  
        headers = {
                    "accept": "application/json",
                    "X-API-Key": X_API_KEY
                }   # token or native
        if net == "ethereum":
            for chain in chains:
                url = "https://deep-index.moralis.io/api/v2/" + address + "/erc20?chain=" + chain            
                if balance_kind == "native":
                    url = "https://deep-index.moralis.io/api/v2/" + address + "/balance?chain=" + chain
                info = requests.get(url, headers=headers)
                result_json = info.json()
                if result_json:
                    if balance_kind == "token":
                        
                        for result in result_json:
                            result_data.append({
                                "Chain" : chain,
                                "Holding amount" : result['balance'],
                                "Crypto name" : result['name'],
                                "crypto logo" : result['logo']
                            })
                    else:
                        result_data.append({
                            "Chain" : chain,
                            "Holding amount" : result_json['balance'],
                            "Crypto name" : None,
                            "crypto logo" : None
                        })
        if(net == 'solana'):
            #for chain in chains:
            url = "https://solana-gateway.moralis.io/account/mainnet/" +  address + "/"
            if balance_kind == "native":
                url += "balance"
            else:
                url += "tokens"
            info = requests.get(url, headers=headers)
            result_json = info.json()
            if result_json:
                if balance_kind == "token":
                    result_data = []
                    for result in result_json:
                        token_address = result['mint']
                        token_url = 'https://public-api.solscan.io/token/meta?tokenAddress=' + token_address
                        token_info = requests.get(token_url,headers=headers)
                        token_json = token_info.json()
                        result_data.append({
                            "Chain" : chain,
                            "Holding amount" : result['amountRaw'],
                            "Crypto name" : token_json['name'],
                            "crypto logo" : token_json['icon']
                        })
                else:
                    result_data = [{
                        "Chain" : net,
                        "Holding amount" : result_json['lamports'],
                        "Crypto name" : None,
                        "crypto logo" : None
                    }]

    return jsonify(result_data),201

@app.route('/getNFTInfo',methods = ['GET','POST'])
def nft_info():
    result_json = []
    result_data = []
    return_data = []

    if not session.get("address"):
            return 'please connect wallet'

    if request.method == 'POST':
        data = json.loads(request.data)
        net = data['net']   # ethereum or solana
        chain = data['chain']   # eth, polygon, bsc
        address = data['address']

        if net == "ethereum":
            for chain in chains:
                url = "https://deep-index.moralis.io/api/v2/" + address +"/nft?chain=" + chain + "&format=decimal"
                headers = {
                        "accept": "application/json",
                        "X-API-Key": X_API_KEY
                    }
                x = requests.get(url, headers=headers)
                result_json = x.json()
                print(chain)
                if result_json['total'] and result_json['total'] > 0:
                    result_data = result_json['result']
                    bPass = False
                    while result_json['cursor']:
                        bPass = True
                        url_real = url + "&cursor=" + result_json['cursor']
                        x = requests.get(url_real, headers=headers)
                        result_json = x.json()
                        #result_data = result_data.extend(result_json['result'])
                        result_data += result_json['result']
                    if bPass == True:
                        result_data += result_json['result']
                        #result_data = result_data.extend(result_json['result'])
                        #temp_data = result_json['result']
                    
                    for result in result_data:
                        #token_name = result['name'].replace(' ','').lower()
                        #url = "https://deep-index.moralis.io/api/v2/nft/" + result['token_address'] + "/lowestprice?chain=" + chain + "&days=7&marketplace=opensea"
                        #price_data = requests.get(url, headers=headers)
                        #price_data = price_data.json()
                        metadata = json.loads(result['metadata'])
                        image = metadata['image']
                        if('ipfs://' in image):
                            image = image.replace('ipfs://','')
                            image = 'https://ipfs.io/ipfs/' + image
                        url = 'https://api.opensea.io/api/v1/asset_contract/' + result['token_address']
                        slug_data = getAPIResponse(url)
                        if(slug_data and slug_data['collection']):
                            slug = slug_data['collection']['slug']
                            url = 'https://api.opensea.io/api/v1/collection/' + slug
                            price_data = getAPIResponse(url)
                            return_data.append({
                                "Floor price from Opensea" : price_data['collection']['stats']['floor_price'],
                                "Source Image URL" : image,
                                "Asset Contract address" : result['token_address'],
                                "Token number" : result['token_id'],
                                "Description" : metadata['description'],
                                "Token standard" : result['contract_type'],
                                "Chain" : chain,
                                "Collection name" : result['name'],
                                "Collection logo" : result['symbol'],
                            })
        if(net == 'solana'):
            url = "https://solana-gateway.moralis.io/account/mainnet/" + address + "/nft"
            headers = {
                    "accept": "application/json",
                    "X-API-Key": X_API_KEY
                }
            x = requests.get(url, headers=headers)
            result_json = x.json()
            for result in result_json:
                token_address = result['mint']
                token_url = 'https://solana-gateway.moralis.io/nft/mainnet/' + token_address + '/metadata'
                token_info = requests.get(token_url,headers=headers)
                token_json = token_info.json()
                token_name = token_json['name']
                print(token_name)
                collections = getAPIResponse(url='https://api.opensea.io/api/v1/collections?asset_owner='+ address +'&offset=0&limit=300')
                for collection in collections:
                    print(collection['name'])
                    if(token_name in collection['name']):
                        slug = collection['slug']
                        break
                nft_data = getAPIResponse('https://api.opensea.io/api/v1/collection/' + slug)
                
                return_data.append({
                    "Floor price from Opensea" : nft_data['collection']['stats']['floor_price'],
                    "Source Image URL" : nft_data['collection']['image_url'],
                    "Asset Contract address" : token_address,
                    "Token number" : token_address,
                    "Description" : nft_data['collection']['description'],
                    "Token standard" : token_json['standard'],
                    "Chain" : net,
                    "Collection name" : token_json['name'],
                    "Collection logo" : token_json['symbol'],
                })
                
    return jsonify(return_data) , 201