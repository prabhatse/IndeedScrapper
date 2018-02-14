
from random import choice
import requests

user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us; Silk/1.1.0-80) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16 Silk-Accelerated=true",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; ARM; Trident/6.0)",
    "Mozilla/5.0 (Windows; U; Win 9x 4.90; en-GB; rv:1.8.1.1) Gecko/20061204 Firefox/2.0.0.1",
    "Mozilla/5.0 (X11; U; SunOS sun4u; en-US; rv:1.6) Gecko/20040503",
    "Mozilla/5.0 (X11; CrOS i686 0.12.433) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.77 Safari/534.30",
]
def random_user_agent():
    return choice(user_agents)

def check_proxy(session, proxy_host):

    response = session.get('https://canihazip.com/s')
    returned_ip = response.text
    print(returned_ip +" "+proxy_host)
    if returned_ip != proxy_host:
        print ("ip was not matched")
        #raise StandardError('Proxy check failed: {} not used while requesting'.format(proxy_host))
    else:
        print(proxy_host+" Its working")

def random_proxy():
    #resp = requests.get("https://gimmeproxy.com/api/getProxy?protocol=http&port=80&country=US")
    resp = requests.get("https://gimmeproxy.com/api/getProxy?protocol=http")
    #resp = requests.get("http://pubproxy.com/api/proxy?limit=1&format=txt&http=true&country=US&type=http")
    #if resp.status_code == 200:
    #    return resp.content
    #return None
    resp = resp.json()
    return {'host':resp['ip'], 'port':resp['port'], 'protocol':resp['protocol']}

def test_proxy():
    proxy = random_proxy()
    print(proxy)
    session = requests.Session()
    session.headers = random_user_agent()
    session.proxies = {'https': "{protocol}://{host}:{port}/".format(**proxy)}
    check_proxy(session, proxy['host'])

if __name__ == '__main__':
    i = 1
    #test_proxy()

    while i < 50:
        i += 1
        try:
            test_proxy()
        except Exception as e:
            continue    
