import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from web3.middleware import geth_poa_middleware

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)

def read_txt(file_path):
    """从文本文件读取私钥。"""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

chain_id = 1942999413  # Humanity Testnet 链 ID33
rpc_url = "https://rpc.testnet.humanity.org/"

def create_web3_with_proxy():
    """为每个代理创建独立的 Web3 实例"""
    http_provider = Web3.HTTPProvider(rpc_url)
    web3 = Web3(http_provider)
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return web3

def claim_rewards(private_key):
    """使用提供的私钥来领取奖励。"""
    # 连接到节点
    w3 = create_web3_with_proxy()
    # 检查连接是否成功
    if not w3.is_connected():
        raise Exception("无法连接到节点。")
    account = w3.eth.account.from_key(private_key)
    sender_address = w3.to_checksum_address(account.address)
    contract_address = w3.to_checksum_address("0xa18f6FCB2Fd4884436d10610E69DB7BFa1bFe8C7")
    transaction_data = "0xb88a802f"  # 领取奖励的方法

    try:
        # 估算 Gas
        gas_estimate = w3.eth.estimate_gas({
            'to': contract_address,
            'data': transaction_data,
            'from': sender_address,
        })
        # 获取当前 Gas 价格
        gas_price = w3.eth.gas_price

        # 构建交易
        transaction = {
            'to': contract_address,
            'value': 0,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(sender_address),
            'chainId': chain_id,
            'data': transaction_data,
        }
        # 对交易进行签名
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        if w3.to_hex(tx_hash):
            print(f'账户 {sender_address} 签到成功')
        time.sleep(1)
    except Exception as e:
        error_str = str(e)
        # 检查并提取 'no rewards available' 信息
        if 'no rewards available' in error_str:
            print(f"账户 {sender_address} 无奖励可领取")
        elif 'user not registered' in error_str:
            print(f"账户 {sender_address} 用户未注册")
        else:
            print(f"账户 {sender_address} 发生其他错误: {error_str}")

def claim_rewards_for_all(private_keys):
    """使用线程池异步处理所有私钥的奖励领取"""
    with ThreadPoolExecutor(max_workers=5) as executor:  # 设置并发数，可以根据需求调整
        future_to_private_key = {executor.submit(claim_rewards, private_key): private_key for private_key in private_keys}
        for future in as_completed(future_to_private_key):
            private_key = future_to_private_key[future]
            try:
                future.result()  # 获取线程执行结果
            except Exception as e:
                print(f"处理私钥 {private_key} 时发生错误: {e}")

def wait_for_next_execution():
    """计算并等待直到下次执行时间"""
    interval = 24 * 60 * 60 + 5 * 60  # 24小时5分钟的秒数
    print("等待下一次执行...")
    time.sleep(interval)  # 等待下次执行

if __name__ == "__main__":
    while True:
        private_keys = read_txt('privates.txt')
        claim_rewards_for_all(private_keys)  # 执行奖励领取操作
        wait_for_next_execution()  # 等待24小时5分钟后再次执行
