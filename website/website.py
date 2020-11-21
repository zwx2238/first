from flask import Flask, request, send_from_directory
import sys

sys.path.insert(0, '..')
from node import *

app = Flask('mindmap')

search_box = """
<div class="search">
<form role="search" method="get" action="http://127.0.0.1:5000/search">
  <input type="search" name="q" autocomplete="off" placeholder="Search" required class="searchform">
</form>
</div>
"""

title_div = '<div class="title">{}<br><br></div>'

clock_div = """
<div id="sp_time"><&nbsp></div>
<script type="text/javascript">
setInterval(function(){
	var dd = new Date();
	var y = dd.getFullYear();
	var m = dd.getMonth() + 1;
	var d = dd.getDate();
	var h = dd.getHours();
	var mi = dd.getMinutes();
	var s = dd.getSeconds();
	var str = y + "年" + m + "月" + d + "日&nbsp;&nbsp;" + h + ":" + mi + ":" + s + "&nbsp;&nbsp;星期" + "日一二三四五六".charAt(dd.getDay());
	document.getElementById("sp_time").innerHTML = str;
},1);
</script>
	"""
# search_box=''
clock_div = '''
<div class="page">
<a href="javascript:history.go(-1);">上一页</a>
<a href="javascript:history.go(1);">下一页</a>
</div>

<div id="bdtts_div_id">
    <audio id="tts_autio_id" autoplay="autoplay">
    </audio>
</div>
'''

with open('css.css') as fp:
    css_file = fp.read()

css = "<style>" + css_file + "</style>"

# <script src="https://code.jquery.com/jquery-3.5.1.js" integrity="sha256-QWo7LDvxbWT2tbbQ97B53yJnYU3WhH/C8ycbRAkjPDc=" crossorigin="anonymous"></script>

# <script>
# $(document).on('click', 'img', function() {
#     $(this).toggleClass('min');
#     $(this).toggleClass('max');
# });
# </script>

js = """
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script> 
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({
    tex2jax: {
      inlineMath: [ ['$','$'], ["\\(","\\)"] ],
      processEscapes: true
    }
  });
</script>

"""
audio_js1 = """
<script>
document.onkeydown=function(event){   
    var e = event || window.event || arguments.callee.caller.arguments[0];   
    if(e && e.keyCode==187){ // 按 Esc    
        //要做的事情   
        doTTS();
    }  
}
function doTTS() {
    var ttsDiv = document.getElementById('bdtts_div_id');
    var ttsAudio = document.getElementById('tts_autio_id');
"""
audio_js2 = """
    // 文字转语音
    ttsDiv.removeChild(ttsAudio);
    var au1 = '<audio id="tts_autio_id" autoplay="autoplay">';
    var sss = '<source id="tts_source_id" src="https://tts.baidu.com/text2audio?cuid=baike&lan=ZH&ctp=1&spd=15&pdt=301&vol=9&rate=32&per=111&tex=' + ttsText + '" type="audio/mpeg">';
    var eee = '<embed id="tts_embed_id" height="0" width="0" src="">';
    var au2 = '</audio>';
    ttsDiv.innerHTML = au1 + sss + eee + au2;

    ttsAudio = document.getElementById('tts_autio_id');

    ttsAudio.play();
}
</script>
"""


@app.route('/search/')
def search_detail_page():
    mode = ''
    q = request.args.get('q')

    if q.endswith('-c'):
        results = search(q[:-2], mode='contains')
    elif q.endswith('-v'):
        results = search(q[:-2], mode='vague')
    elif q.endswith('-f'):
        results = [search(q[:-2], mode='full_path')]
    else:
        if q.endswith('-a'):
            q = q[:-2]
            mode = 'all'
        results = search(q, mode='strict')
        if not results:
            results = search(q, mode='vague')
        if not results:
            results = search(q, mode='contains')

    if len(results) == 1:
        result = results[0]

        if mode == 'all':
            recursion = True
        else:
            recursion = False

        top_box = search_box + title_div.format(result) + clock_div

        # global js
        # if result.has_meta_child:
        #     audio_text = ''
        #     audio_text = result.children[0].children[0].full_text
        # else:
        #     audio_text = '暂无音频'

        # js += audio_js1 + 'var ttsText = "{}";'.format(audio_text) + audio_js2

        return css + js + top_box + result.html_header() + '<div class="body">' + result.html_body(
            result, recursion=recursion) + '</div>'

    elif len(results) == 0:
        top_box = search_box + title_div.format(q) + clock_div

        return css + js + top_box + '<br>没找到'

    elif len(results) > 1:
        top_box = search_box + title_div.format(q) + clock_div

        response = css + js + top_box
        for result in results:
            response += '<br>' * 2 + result.create_tag(ex_string=result.full_path)

        return response


app.debug = True
if __name__ == '__main__':
    app.run()
