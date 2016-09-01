import tornado.web


class ItemModule(tornado.web.UIModule):
    def render(self, item):
        return self.render_string('modules/item.html', item=item)


class PicContentModule(tornado.web.UIModule):
    def render(self, pics_dict):
        return self.render_string('modules/pic_content.html', pics_dict=pics_dict)


class PicModule(tornado.web.UIModule):
    def render(self, prefix, pics):
        return self.render_string('modules/pic.html', prefix=prefix, pics=pics)


