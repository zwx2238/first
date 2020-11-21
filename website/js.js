function changetext(s){
	var name=$(s).children("a").text();
	$(s).html("");
	$(s).parent().append("<input value='"+name+"' onkeydown='submit(this)'/>");
	// $(s).parent().children("input").attr("onblur","nameblur(this,'"+name+"')");
	$(s).parent().children("input").focus();
	$(s).remove();
}

function submit(s){
	if(event.key!='Enter') return;
	var changed_text=s.value;
	
	loadDoc();


	$(s).html("");
	$(s).parent().append("<div onclick='changetext(this)'><a>"+changed_text+"</a></div>");
	$(s).remove();
}

function loadDoc() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
     document.getElementsByClassName("search")[0].innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "Note.txt", true);
  xhttp.send();
}