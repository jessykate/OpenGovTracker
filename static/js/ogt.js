
$(document).ready(function() {
  $("#agency_table").tablesorter({
    headers: {
      5: { sorter: false }
    }
  });
});


function toggle_visible(agency_link) {
  // get the link to the agency we want to make visible
  var agency = agency_link.getAttribute("href");
  agency_link.style["font-weight"] = "bold";

  // strip the leading #
  var visible_agency = agency.slice(1,agency.length);

  var report_section = document.getElementById("reports");
  var reports = report_section.getElementsByTagName("div");
  for (var i=0; i< reports.length; i++) {
    var link = reports[i].getElementsByTagName("a")[0];
    var agency_name = link.getAttribute("name");
    if (agency_name == visible_agency) {
      reports[i].style.display="";
    }
    else {
      link.style["font-weight"] = "normal";
      reports[i].style.display="none";
    }
  }
};

window.onload = function() {
  // register the toggle function with the agency links
  var agency_list = document.getElementById("agency_options");
  var agency_links = agency_list.getElementsByTagName("a");
  for (var i=0; i< agency_links.length; i++) {
    agency_links[i].onclick=function() {
    toggle_visible(this);
    return false;
    };
  }

  // disable display of each agency's report to start
  var reports_section = document.getElementById("reports");
  var agency_sections = reports_section.getElementsByTagName("div");
  for (var i=0; i< agency_sections.length; i++) {
    agency_sections[i].style.display="none";
  }
};

