import re
import urllib.parse

space = '&nbsp'
new_line = '<br>'
delimiter = '|'
# max_width = 1920 // (1.5 * 16) - 12
max_width = 50
indents = 8
blank_line = '<div class="blank">' + new_line + '</div>'

# line_width = 100
# begin_indents = 16

FULL_PATH_DELIMITER = '/'
ROOT_PATH = ''
LINK_SYMBOL = ' >'
MAX_DEPTH = 100


class Node:
    prefix = 'http://127.0.0.1:5000/search/?q='
    suffix = '+-f'
    tag = """<{0} {1}>{2}</{0}>"""
    a_tag_leaf = """<a href={2}http://127.0.0.1:5000/search/?q={0}{2}>{1}</a>"""

    def __init__(self, text, link):
        self.text = text
        self.link = link
        self.parent = None
        self.children = []

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        return self.text == other.text

    # path text
    def set_default_full_path(self):
        """
            需在确立父节点后才能获取full_path
            full_path不包含ROOT
        """
        node_ptr = self
        full_path = []
        while node_ptr.text != 'ROOT':
            full_path.append(node_ptr.text)
            node_ptr = node_ptr.parent
        return FULL_PATH_DELIMITER.join(full_path[::-1])

    @property
    def full_link_path(self):
        node_ptr = self
        full_path = []
        while node_ptr.text != 'ROOT':
            if node_ptr.link:
                full_path.append(node_ptr.text)
            node_ptr = node_ptr.parent
        return '--'.join(full_path[::-1])

    @property
    def site_text(self):
        text = self.text
        if text.endswith(' .'):
            text = text[:-2]
        elif text.endswith(' ..'):
            text = text[:-3]
        if self.link:
            text += ' {}'.format(len(self.children))

        d = {' ': space, '>': '&gt;', '<': '&lt;'}

        for key, value in d.items():
            text = text.replace(key, value)

        return text

    @property
    def site_href(self):
        text = self.text
        full_path = self.full_path

        if text.startswith("url:"):
            href = text[4:].strip()
        elif text.startswith("file:"):
            href = 'http://192.168.137.1:8887/Users/python/Desktop/files/' + text[5:].strip()
        elif text.endswith(' .'):
            href = self.prefix + text[:-2]
        else:
            href = self.prefix + full_path + self.suffix
        # elif href.endswith(' ..'):
        #     href = href[:-3]
        # if self.link:
        #     href += ' {}'.format(len(self.children))

        # d = {' ': space, '>': '&gt;', '<': '&lt;'}

        # for key, value in d.items():
        #     href = href.replace(key, value)

        return href
    @property
    def full_text(self):
        full_text = self.to_txt_string(recursion=True)
        if full_text.startswith('audio:'):
            full_text = full_text[6:]

        full_text = re.sub('\s','',full_text)
        # print(full_text)

        return full_text
    # search
    def strict_search(self, query):
        keywords = query.split()

        results = []
        last_result = None
        for link_node in self.all_sub_link_nodes(max_depth=MAX_DEPTH):  # 在所有link_node下搜索
            # matched_results = []
            for node in link_node.all_sub_page_nodes():  # 只搜索当前子导图
                if last_result and node.is_sub_node_of(last_result):  # 排除匹配节点的子节点
                    continue

                if node.strict_match(keywords):
                    results.append(node)
                    last_result = node
        return results

    def strict_match(self, keywords):
        if keywords[-1] != self.text.lower():
            return False

        full_path = self.full_path.lower().split(FULL_PATH_DELIMITER)  # 与节点内容匹配
        for keyword in keywords:
            if keyword not in full_path:
                return False

        return True

    def is_sub_node_of(self, parent):
        return self.full_path.startswith(parent.full_path)

    def contains_search(self, query):
        keywords = query.split()
        results = []
        for node in self.all_sub_nodes(max_depth=MAX_DEPTH):
            if node.contains_match(keywords):
                results.append(node)
        return results

    def contains_match(self, keywords):
        """
            可添加同义词搜索功能，暂未实现
        """
        if keywords[-1] not in self.text:
            return False

        for keyword in keywords:
            if keyword not in self.full_path.lower():
                return False

        return True

    def vague_search(self, query):
        keywords = query.split()
        results = []
        for node in self.all_sub_nodes(max_depth=MAX_DEPTH):
            if node.vague_match(keywords):
                results.append(node)
        return results

    def vague_match(self, keywords):
        """
            可添加同义词搜索功能，暂未实现
        """
        if keywords[-1] not in re.split("/| ", self.text.lower()):
            return False

        if self.text.endswith(' .'):
            return False

        full_path = self.full_path.lower()  # 在节点内容中
        for keyword in keywords:
            if keyword not in re.split("/| ", full_path):
                return False

        return True

    def full_path_search(self, full_path):
        # 兄弟节点不能重名，否则full_path不唯一
        for node in self.all_sub_nodes(search_end=True, max_depth=MAX_DEPTH):
            if node.full_path == full_path:
                return node

    def is_end(self):
        if self.text.startswith(('link:',)):
            return True
        if self.parent and self.parent.text.startswith(('code:', 'formula:')):
            return True
        return False

    def all_sub_nodes(self, depth=0, search_end=False, *, max_depth):
        if not search_end and self.is_end():
            return

        if depth > max_depth:
            return

        yield self
        for child in self.children:
            yield from child.all_sub_nodes(depth + 1, search_end=search_end, max_depth=max_depth)

    def all_sub_link_nodes(self, depth=0, search_end=False, *, max_depth):
        if not search_end and self.is_end():
            return

        if depth > max_depth:
            return

        if self.link:
            yield self
        for child in self.children:
            if child.link:
                yield from child.all_sub_link_nodes(depth + 1, max_depth=max_depth)
            else:
                yield from child.all_sub_link_nodes(depth, search_end=search_end, max_depth=max_depth)

    def all_sub_page_nodes(self, search_end=False):
        if not search_end and self.is_end():
            return
        yield self
        for child in self.children:
            if not child.link:
                yield from child.all_sub_page_nodes(search_end=search_end)

    # website
    @staticmethod
    def to_href(href):
        # d = {'+': '%2B', '&': '%24'}
        # for k, v in d.items():
        #     href = href.replace(k, v)
        return urllib.parse.quote(href)

    @staticmethod
    def to_site_text(string):
        # if string.endswith(' .'):
        #     string = string[:-2]
        # elif string.endswith(' ..'):
        #     string = string[:-3]

        # if self.link:
        #     string += ' {}'.format(len(self.children))

        d = {' ': space, '>': '&gt;', '<': '&lt;'}

        for key, value in d.items():
            string = string.replace(key, value)

        return string

    def create_tag(self, level=0, ex_string=None, replace=True):

        tag_name = 'a'
        attrs = {}
        string = level * indents * space

        prefix = 'http://127.0.0.1:5000/search/?q='
        strict_suffix = '+-f'

        link_prefix = '-> '
        link_prefix = ''

        code_prefix = 'code:'
        code_prefix = ''

        full_path = Node.to_href(self.full_path)

        if self.text.startswith('url:'):
            url_string_list = self.text[4:].strip().split(' ', 1)
            url_string = url_string_list[-1]
            attrs['href'] = url_string_list[0]
            attrs['target'] = '_blank'
            string += url_string
            attrs['class'] = 'url'

        elif self.text.startswith('link:'):
            link_url = self.text[5:].strip().split(' ',1)[0]
            link_string = self.text[5:].strip().split(' ',1)[-1]
            attrs['href'] = prefix + link_url.replace('-', ' ')
            string += link_prefix + link_string
            attrs['class'] = 'link'

        # elif self.text.startswith(('code:', 'formula')):
        #     attrs['href'] = prefix + full_path + strict_suffix
        #     string += code_prefix + self.text.split(':', 1)[-1].strip()
        #     attrs['class'] = 'end'
        # elif self.text.startswith(('audio:')):
        #     audio_src = 'http://127.0.0.1:8887/audio/' + self.text[6:].strip()
        #     # mattrs = ' '.join(["{0}={2}{1}{2}".format(key, value, self.get_quoto()) for key, value in mattrs.items()])
        #
        #     audio_string = '<source src="{}" type="audio/mpeg">'.format(audio_src)
        #
        #     audio_tag = self.tag.format('audio', 'controls', audio_string)
        #     string += audio_tag
        #     replace = False
        # elif self.text.startswith('img:'):
        #     iattrs = {}
        #     iattrs['src'] = 'http://127.0.0.1:8887/img/' + self.text[4:].strip()
        #     iattrs['alt'] = self.text[4:].strip()
        #     iattrs['class'] = 'min'
        #     iattrs['id'] = 'img'
        #     iattrs = ' '.join(["{0}={2}{1}{2}".format(key, value, self.get_quoto()) for key, value in iattrs.items()])
        #
        #     img_tag = self.tag.format('img', iattrs, '')
        #     string += img_tag
        #     replace = False
        elif self.link and len(self.children):
            attrs['href'] = prefix + full_path + strict_suffix
            string += self.text
            attrs['class'] = 'link_node'
        else:
            attrs['href'] = prefix + full_path + strict_suffix
            string += self.text

        if ex_string:
            string = ex_string
        if replace:
            string = Node.to_site_text(string)
        attrs = ' '.join(["{0}={2}{1}{2}".format(key, value, self.get_quoto()) for key, value in attrs.items()])

        # raise Exception('attrs',attrs)

        # if text:
        #     tmp_text = text
        # else:
        #     tmp_text = self.site_text
        #
        # if href:
        #     tmp_href = href
        # else:
        #     tmp_href = self.site_href

        # try 2
        # current_indents = len(tmp) - len(tmp.strip()) + begin_indents + 3
        # a_text = space * (len(tmp) - len(tmp.strip()))
        #
        # cnt = len(a_text)
        # for word in tmp.split():
        #     if len(word) + cnt > line_width:
        #         a_text += new_line + current_indents * space
        #     a_text += word + space
        #     cnt = (cnt + len(word)) % line_width
        # try 1
        # for i in range(0, len(tmp), line_width):
        #     end = i + line_width if i + line_width < len(tmp) else len(tmp)
        #
        #     if end != len(tmp):
        #         a_text += tmp[i:end].replace(' ', space) + new_line + (
        #                     len(tmp) - len(tmp.strip()) + begin_indents) * space
        #     else:
        #         a_text += tmp[i:end].replace(' ', space)

        # return self.tag.format(tmp_href, tmp_text, self.get_quoto())
        return self.tag.format(tag_name, attrs, string)

    def get_quoto(self):
        return "'" if '"' in self.full_path else '"'

    def html_header(self):
        html_header = ''

        html_header += self.html_parents()+"<hr>"
        html_header += self.html_siblings()+"<hr>"
        # html_header += self.html_subs()
        # html_header += self.html_links()

        return html_header

    def html_parents(self):
        parents = []
        node_ptr = self
        while node_ptr and node_ptr.text != "ROOT":
            parents.append(node_ptr)
            node_ptr = node_ptr.parent

        return self.html_div(parents[::-1], 'parents')

    def html_siblings(self):
        return self.html_div(self.parent.children, 'siblings')

    def html_subs(self):
        return self.html_div(self.children, 'subs')

    def html_links(self):
        return self.html_div(self.all_sub_link_nodes(max_depth=1), 'links')

    def html_div(self, nodes, div_class):
        blank_line = ''
        nodes = list(nodes)

        div = '<div class="{0}"><div>'.format(div_class)
        if (div_class in ('subs', 'siblings') and (
                len(nodes) > 10 or len(nodes) == 0 or self.text.endswith(('.py', '.c')))) or (
                div_class == 'links' and (len(nodes) <= 1)):
            nodes = []
        # div += '<div class="text"><br></div>'

        cnt = 0
        op = 0

        for node in nodes:
            if div_class == 'links' and node.full_path == self.full_path:
                continue

            alnum_text, length1 = re.subn("[\u4e00-\u9fa5]", "", node.text)
            if alnum_text.endswith(" >"):
                alnum_text = alnum_text[:-1].strip()
            if alnum_text.endswith((" .")):
                alnum_text = alnum_text[:-1].strip()
            length = len(alnum_text) / 2 + length1 + 2.5 + len(str(len(node.children)))

            if cnt + length > max_width:
                div += '</div> <div>'
                cnt = 0
                op = 1

            div += node.create_tag() + space + delimiter + space
            cnt += length

        div += blank_line

        # return div + '</div></div>'+'<div class="hr"><hr></div>'
        return div + '</div></div>'

    def html_body(self, root, level=0, recursion=False):
        html_body = ""

        # if self.meta:
        #     return html_body

        link_string = '>' if self.link else ''

        if self.full_path == root.full_path:
            link_string = ''

        # line = self.site_text + ' ' + link_string

        line = self.site_text
        blank_line = ''

        tag = self.create_tag(level)
        html_body = '<div class="text">' + '<div">' + tag + '</div>' + '</div>' + blank_line

        if level == 0 or recursion or not self.link:
            for child in self.children:
                html_body += child.html_body(root, level + 1, recursion)

        return html_body

    # sublime
    def update_links_from(self, original_node):
        """
            按照original_node中的link更新changed中的link
        """
        changed = self

        original_linked_nodes = original_node.all_sub_link_nodes(max_depth=1)
        changed_linked_nodes = changed.all_sub_link_nodes(max_depth=MAX_DEPTH)

        original_links_dict = {}

        for linked_node in original_linked_nodes:
            original_links_dict[linked_node.text] = linked_node

        for linked_node in changed_linked_nodes:
            if linked_node.text != changed.text and linked_node.text in original_links_dict:
                for child in original_links_dict[linked_node.text].children:
                    linked_node.children.append(child)

    def save_to_txt(self, path):
        with open(path, 'w', encoding='utf8') as fp:
            fp.write(self.to_txt_string(recursion=True))

    def to_txt_string(self, level=0, *, recursion):
        islink = LINK_SYMBOL if self.link else ''
        string = '\t' * level + self.text + ' ' + islink + '\n\n'
        if level == 0 or recursion or not self.link:
            for child in self.children:
                string += child.to_txt_string(level + 1, recursion=recursion)
        return string


# global
def load_txt(path):
    with open(path, encoding='utf8') as fp:
        note = fp.read()
        return to_tree(note)


def to_tree(note):
    last_level = -1
    root_node = Node('ROOT', False)
    last_node = root_node
    parent_node = root_node
    for line in note.split('\n'):
        if not line.strip():
            continue
        text, link, level = process_line(line)
        node = Node(text, link)
        if level > last_level + 1:
            raise Exception('缩进层次跳跃' + text)
        elif level == last_level + 1:
            parent_node = last_node
        else:
            for i in range(last_level - level):
                parent_node = parent_node.parent

        # if node.text.startswith('meta:'):
        #     node.meta = True
        #     parent_node.has_meta_child = True
        # else:
        #     node.meta = False

        # node.has_meta_child = False
        node.parent = parent_node
        parent_node.children.append(node)

        node.full_path = node.set_default_full_path()

        last_level = level
        last_node = node

    return root_node.children[0]


def process_line(line):
    line = line.rstrip()
    if line.endswith(LINK_SYMBOL):
        link = True
        line = line[:-2].rstrip()
    else:
        link = False
    line, level = re.subn('\t', '', line)

    if line.startswith(' '):
        raise Exception('缩进中含有空格' + line)  # 混入空格将引起层次错乱
    return line, link, level


def search(query, *, mode):
    query = query.strip()
    root_node = load_txt(ROOT_PATH)
    if mode == 'strict':
        return root_node.strict_search(query.lower())
    elif mode == 'vague':
        return root_node.vague_search(query.lower())
    elif mode == 'contains':
        return root_node.contains_search(query.lower())
    elif mode == 'full_path':
        return root_node.full_path_search(query)
    else:
        raise Exception('未定义的搜索模式：' + mode)


def alter(changed):
    root_node = load_txt(ROOT_PATH)
    original_node = root_node.full_path_search(changed.full_path)

    changed.update_links_from(original_node)

    parent = original_node.parent
    pos = parent.children.index(original_node)
    parent.children[pos] = changed

    if changed.text == 'Note':
        return parent.children[0]  # 如果是修改主页，new_root不再是root_node
    else:
        return root_node


def init():
    global ROOT_PATH
    d = {}
    with open('Note.ini') as fp:
        for line in fp:
            key, value = line.split('=')
            d[key] = value
        ROOT_PATH = d['ROOT_PATH']
        ROOT_PATH = ROOT_PATH + 'Note.txt'


init()

if __name__ == '__main__':
    root_node = load_txt(ROOT_PATH)

# test for full_path search
# result = search('Note/数学', mode='full_path')
# result.save_to_txt('result.txt')

# test for all_nodes
# print(list(root_node.all_sub_nodes(max_depth=2)))
# print(list(root_node.all_sub_link_nodes(max_depth=2)))
# print(list(root_node.all_sub_page_nodes()))

# test for strict search
# results = search('Note 数学', mode='strict')
# for result in results:
#     print(result.full_path)

# test for vague search
# results = search('1', mode='vague')
# for result in results:
#     print(result.full_path)

# test for alter
# changed = load_txt('Note1.txt')
# changed.full_path='Note'
# new_root = alter(changed)
# print(new_root.to_txt_string())

# root_node=load_txt(ROOT_PATH)
# print(root_node.to_links(root_node,space=' ',new_line='\n'))
