
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

  // strip the leading # in the href value
  var visible_agency = agency.slice(1,agency.length);

  /* get only the child *elements* of the reports section. don't use
   getElementsByTagName() because it will grab all nested div's, too,
   which will screw up the display toggling. */
  var report_section = document.getElementById("reports");
  var report_children = report_section.childNodes;
  var reports = Array();
  for (var i=0; i<report_children.length; i++) {
    if (report_children[i].nodeType == 1) {
      reports.push(report_children[i]);
    }
  }

  // make the selected agency report visible, suppressing the rest
  for (var i=0; i< reports.length; i++) {
    var link = reports[i].getElementsByTagName("a")[0];
    var agency_name = link.getAttribute("name");
    if (agency_name == visible_agency) {
      reports[i].style.display="";
      link.style.fontWeight = "bold";
    }
    else {
      link.style.fontWeight = "none";
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

  /* show the summary table but disable display of agency-specific
   * reports to start */
  var report_section = document.getElementById("reports");
  var report_children = report_section.childNodes;
  var reports = Array();
  for (var i=0; i<report_children.length; i++) {
    if (report_children[i].nodeType == 1) {
      reports.push(report_children[i]);
    }
  }
  for (var i=0; i< reports.length; i++) {
    if (reports[i].getAttribute("id") != "summary_table") {
      reports[i].style.display="none";
    }
  }
};

