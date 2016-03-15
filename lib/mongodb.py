import pymongo

def client(url, port):
    return pymongo.MongoClient(url, port)

def coll_insert(coll, doc):
    count = coll.find(doc).count()
    if count > 0:
        pass
    else:
        coll.insert(doc)

def coll_findone(coll, key):
    return coll.find_one(key)

def coll_find(coll, key):
    return [item for item in coll.find(key)]

def coll_findall(coll):
    return [item for item in coll.find()]
