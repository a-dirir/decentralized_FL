from mongoengine import Document, IntField, DictField, ListField, StringField


class Node(Document):
    node_id = IntField(required=True, primary_key=True)
    pek = StringField(required=True)
    psk = StringField(required=True)
    node_info = DictField(required=True)

    meta = {'collection': 'Nodes'}


class Process(Document):
    process_id = IntField(required=True, primary_key=True)
    owner = IntField(required=True)
    process_info = DictField(required=True)
    participants = ListField(DictField(), default=list)

    meta = {'collection': 'Processes'}


