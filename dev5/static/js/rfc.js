var editRFC = function() {
    document.getElementById('body').innerHTML = '<div id="aceInstance"></div>';
    document.getElementById('menuBarDynamic').innerHTML = '';
    
    document.title = inventoryObject.name;
    document.getElementById('bodyTitle').innerHTML = inventoryObject.type.toUpperCase() + ': ' + inventoryObject.name;
    $('.nav-tabs a[href="#attributes"]').tab('show');
    
    initAttributes();
    addAttributeText('RFC UUID', 'objuuid');
    addAttributeTextBox('RFC Name', 'name');
    addAttributeTextBox('RFC Title', 'title');
    addAttributeTextBox('RFC Number', 'number');
    addAttributeTextArea('Description', 'description');
    addAttributeTextBox('POC Name', 'poc name');
    addAttributeTextBox('POC Email', 'poc email');
    addAttributeTextBox('POC Phone', 'poc phone');
    
    loadRequiresGrid();
    loadProvidesGrid();
}

var loadAndEditRFC = function(objuuid) {
    document.getElementById('body').innerHTML = '<div id="aceInstance"></div>';
    document.getElementById('menuBarDynamic').innerHTML = '';
    
    $.ajax({
        'url' : 'inventory/ajax_get_object',
        'dataType' : 'json',
        'method': 'POST',
        'data' : {'objuuid' : objuuid},
        'success' : function(resp) {
            inventoryObject = resp;
            editRFC();
            expandToNode(inventoryObject.objuuid);
        }
    });
}