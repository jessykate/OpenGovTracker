# store info necessary to retrieve and parse info about each agency.

agencies = {
    "usaid": "b9b85bb0-5588-4ac3-8a5c-0271851e2130",
    "commerce":"d4d38eba-0c12-4bd4-a4e2-e20494a86b22",
    "defense": "3582db25-510d-48fe-85d2-479d6406535e",
    "education": "76330bcb-fcf3-421c-bd87-bf593e3ebce3",
    "energy": "2574a2ec-c7f7-4477-9a30-3fb268794682",
    "nasa":"519f0a2f-4ac7-4ae2-ac11-8a11d0d9657e",   
}
#    'dot': "",
#    "interior": "",
#    "veterans": "",
#    "treasury": ""
#    "gsa": "",
#    "opm": "",
#    "labor": "",
#    "justice": "",
#    "socialsecurity": "",
#    "state": "",
#    "nsf": "",
#    "hud": "",
#    "epa": "",
#    "sba": "",
#    "homelandsecurity": "",
#    "nrc": "",
#    "ostp": "",
#}

# yes the freaking categories are DIFFERENT FOR EVERY SINGLE AGENCY. $*%@*!#*$%&
cat_id = {
    'usaid': {11832: 'transparency' , 11833: 'participation', 11834:'collaboration', 11835: 'innovation', 11836: 'site_feedback'}, 
    'commerce': {11860: 'transparency', 11861: 'participation', 11862: 'collaboration', 11863: 'innovation', 11864: 'site_feedback'}, 
    'defense': {11865: 'transparency', 11866: 'participation', 11867: 'collaboration', 11868: 'innovation', 11869: 'site_feedback'}, 
    'education': {11870: 'transparency', 11871: 'participation', 11872: 'collaboration', 11873: 'innovation', 11874: 'site_feedback'}, 
    'energy': {11808: 'transparency', 11809: 'participation', 11810: 'collaboration', 11811: 'innovation', 11812: 'site_feedback'}, 
    'nasa': {11571: 'transparency', 11572: 'participation', 11573: 'collaboration', 11928: 'innovation', 11929: 'site_feedback'}, 
}

#cat_id = {
#    'usaid': {'transparency': 11832 , 'participation' 11833: , 'collaboration': 11834, 'innovation': 11835, 'site_feedback':11836}, 
#    'commerce': {'transparency': 11860, 'participation': 11861, 'collaboration': 11862, 'innovation': 11863, 'site_feedback': 11864 }, 
#    'defense' {'transparency': 11865, 'participation': 11866, 'collaboration': 11867, 'innovation': 1186, 'site_feedback': 11869 }, 
#    'education': {'transparency': 11870, 'participation': 11871, 'collaboration': 11872, 'innovation': 11873, 'site_feedback': 11874 }, 
#    'energy': {'transparency': 11808, 'participation': 11809, 'collaboration': 11810, 'innovation': 11811, 'site_feedback': 11812 }, 
#    'nasa': {'transparency': 11571, 'participation': 11572, 'collaboration': 11573, 'innovation': 11928, 'site_feedback': 11929 }, 
#}
