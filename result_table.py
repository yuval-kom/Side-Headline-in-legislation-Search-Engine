from flask_table import Table, Col

class ItemTable(Table):
    point_title = Col('כותרת צד')
    law_title = Col('שם החוק')
    content = Col('תוכן')
    classes = ["table-primary", "table table-bordered", "table-striped"]

# Get some objects
class Item(object):
    def __init__(self, point_title, law_title, content):
        self.law_title = law_title
        self.point_title = point_title
        self.content = content

