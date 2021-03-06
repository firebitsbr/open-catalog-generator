#!/usr/bin/python
import sys
import datetime

active_content_file = sys.argv[1]
data_dir = sys.argv[2]
build_dir = sys.argv[3]
last_update_file = sys.argv[4]
darpa_links = sys.argv[5]
date = datetime.datetime.now()
formatted_date = date.strftime("%B") + " " + date.strftime("%d") + ", " + date.strftime("%Y")

print """
Active content file: %s
Data directory: %s
Build directory: %s
Last Update file: %s
DARPA links: %s
Date: %s
""" % (active_content_file, data_dir, build_dir, last_update_file, darpa_links, date)

def search_head():
  return """
  <!DOCTYPE html>
  <html lang='en'>
  <head>
  <meta http-equiv='Content-Type' content='text/html; charset=utf-8' />
  <title>DARPA - Catalog Search</title>
  <script type='text/javascript' src='jquery-1.9.1.js'></script>
  <script type='text/javascript' src="jstorage.js"></script>
  <script type='text/javascript' src="mustache.js"></script>
  <script type='text/javascript' src="lunr.js"></script>
  <script type='text/javascript' src="utils.js"></script>
  <script type='text/javascript' src="spin.js"></script>  
  <script id="results-table-template" type="text/mustache"></script>
  
  <link rel="stylesheet" type="text/css" href="css/catalog_search.css"/>
  <link rel='stylesheet' href='css/header_footer.css' type='text/css'/>  
  </head>
  
  <body>
"""

def search_html():
  html = "<header class='darpa-header'><div class='darpa-header-images'><a href='http://www.darpa.mil/'><img class='darpa-logo' src='darpa-transparent-v2.png'></a><a href='index.html' class='programlink'><img src='Open-Catalog-Single-Big.png'></a></div>"
  html += "<div class='darpa-header-text no-space'><span><font color='white'> / </font><a href=\"catalog_search.html\"' class='programlink visheader'>Catalog Search</a></span></div></header>"

  html += """
  <div id='page-content'>
	<div id="search-wrap">
		<div class="controls">
		  <input id="search_box" type="search"></input>
		  <button id="search_button">Search</button>
		  <div id="results-heading"></div>
		</div>
		<div class="results">
		  <div id='results-container'></div>
		</div>
	</div>
  </div>  
  """
  return html
  
def search_script(): 
  return """
  <script type='text/javascript'>
    $(document).ready(function () {
		var programs = getPrograms();
		var count = 0;
		var headers = ["id", "Type", "Display Name"];
		var results = [];
		var query_term = '';
		var spinner = new Spinner().spin(); //timeline loading spinner graphic
		
		$(function() {
			$("#results-container").append(spinner.el);
			var param_term = $.jStorage.get("searchTerm");
			if(param_term){
				$('#search_box').val(param_term);
				$('#search_button').click();
			}
		});
		
		for (program in programs){
			var program_nm = programs[program]["Program Name"];
			var program_office = programs[program]["DARPA Office"];

			if(programs[program]["Software File"] != ""){
				var program_sw_details = getDetails(programs[program]["Software File"]);
				var sw_projects = restructureDetails(program_sw_details, "Software", program_office);
				var i = sw_projects.length, key;
				while (i--) { key = sw_projects[i]; results.push(key); }
			  
			}

			if(programs[program]["Pubs File"] != ""){
				var program_pub_details = getDetails( programs[program]["Pubs File"]);
				var pub_projects = restructureDetails(program_pub_details, "Publication", program_office);
				var i = pub_projects.length, key;
				while (i--) { key = pub_projects[i]; results.push(key); }
			}
			
			if(programs[program]["Data File"] != ""){
				var program_data_details = getDetails( programs[program]["Data File"]);
				var data_projects = restructureDetails(program_data_details, "Data Set", program_office);
				var i = data_projects.length, key;
				while (i--) { key = data_projects[i]; results.push(key); }
			}
		}
		
		function restructureDetails(data, type, office){
			project_details = data.map(function (raw) {
				var res = {};
				res["id"] = count++;
				res["Type"] = type;
				res["Office"] = office;
				for (var key in raw){
					if(key == "Software" || key == "Title" || key == "Data Set Name" ){
						if(type == "Data Set"){
							res["Display Name"] = raw["Data Set Name"];
							res["URL Link"] = raw["DARPA Program"] + ".html?tab=tabs2";
						}
						else if(type == "Publication"){
							res["Display Name"] = raw["Title"];
							res["URL Link"] = raw["DARPA Program"] + ".html?tab=tabs1";
						}
						else{
							res["Display Name"] = raw["Software"];
							res["URL Link"] = raw["DARPA Program"] + ".html?tab=tabs0";
						}
					}
					else if(key == "Description"){
							res["Description"] = raw["Description"].replace(/\<br\/\>/g, "\\r\\n");
					}
					else if(key == "Team"){
							res["Team"] = raw["Team"].replace(/\//g, " ");
					}
					else
						res[key] = raw[key];
					
					//If this header is not already in the header array, then add it
					if(!(headers.indexOf(key) > -1))
						headers.push(key);
				}
				return res;
			});
			
			return project_details;
		}

		//console.log(results);
	    // set up the index, specifying the fields of the documents.
		var idx = lunr(function () {
			for(var i=0; i<headers.length; i++){
				  var field = headers[i];

				  if (field == 'id')
					this.ref(field)
				  else if(field == "Description")	
					this.field(field, { boost: 100 }) //description is second highest relevance
				  else if(field == "Display Name")	
					this.field(field, { boost: 200 }) //name is of highest relevance
				  else
					this.field(field)
			 }
			 return this;
		})
		
		//console.log(idx);
		
		var template = "<div id='results-table'>{{#results}}";
		template += "<div data-question-id='{{id}}'>";
		template += "<h3 class='project_header'><a href='{{URL Link}}&term={{Display Name}}' >{{Display Name}}</a></h3>";
		template += "<p class='project_path'>{{Office}} | {{DARPA Program}} | {{Type}}</p>";
		template += "<p class='project_description'>{{Description}}</p>";
		template += "</div><br>";
		template += "{{/results}}</div>";
		
		$("#results-table-template").text(template);

		
		// load the results table template
		var resultsTableTemplate = $("#results-table-template").text()
	   
	   
		//fetch the results
		var renderResultsTable = function (rs, term) {
			$("#results-heading").empty();
			$("#results-heading").append('<p style="float:left; width:60%;"> Search Results for : "' + query_term + '"</p><p style="float:right; width:20%; text-align:right;">Total Results : ' + rs.length + '</p>');
			$("#results-heading").css("border-bottom", "2.5px solid #708284");
			$("#results-container").empty();
			$("#results-container").append(Mustache.to_html(resultsTableTemplate, {results: rs}));
			
			//var new_html = $("#results-container").html().replace(/term/g, '<span style="background-color:yellow;">' + term + '</span>');
			//$("#results-container").html(new_html);
		}
		
		results.forEach(function (record) {
			idx.add(record)
		})
		
		$("#results-table").hide();

		//timer for searching the index
        var debounce = function (fn) {
			var timeout; 
			return function () {
				var args = Array.prototype.slice.call(arguments),
					ctx = $('#search_box')
					
				clearTimeout(timeout)
				timeout = setTimeout(function () {
				  fn.apply(ctx, args);
				  if (ctx.val() == ""){
					$("#results-table").css({'display' : 'none'});
				  }
				  else{
					//console.log("return query results");
					$("#results-table").css({'display' : 'inline'});
					}
					
				}, 200)
			}
        }
		
		$('#search_button').bind('click', debounce(function () {
			  $("#results-container").empty();
			  $("#results-container").append(spinner.el);
			  query_term = $('#search_box').val()
			  $.jStorage.set("searchTerm", query_term);
			  var match = "";
			  var documents = idx.search(query_term).map(function (result) { 
				return results.filter(function (q) {
					match += result.ref + ","; return q.id === parseInt(result.ref, 10) 
				})
			  [0]});

			 // console.log(documents);
			  documents.sort(sortByProperty('Display Name'));
			  renderResultsTable(documents, query_term)	
        }))
		
		$("#search_box").keyup(function(event){
			if(event.keyCode == 13)
				$('#search_button').click();
		});
    })
</script>
"""