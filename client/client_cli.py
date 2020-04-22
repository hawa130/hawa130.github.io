import requests

requrl = 'https://abnyvjny.api.lncldglobal.com/1.1/classes/content'
headers = {
    'Content-Type':'application/json',
    'X-LC-Id':'ABnYvjnyRufm05kdQu2SzSFj-MdYXbMMI',
    'X-LC-Key':'PhiYpUWiyAgVwKJIizK8tD8u'
}

def post(content, poster):
    print(content, poster)
    data = {
        'content':content,
        'author':poster,
    }
    req = requests.post(requrl, json = data, headers = headers)
    print(req.status_code)

def getData(skip, num): #获取 (skip, skip+num] 的数据
    get = requests.get('%s?order=-createdAt&limit=%d&skip=%d&count=1' % (requrl, num, skip), headers = headers)
    get.encoding = 'utf-8'
    result = loads(get.text)
    return result