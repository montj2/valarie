var editSchedule = function() {
    document.getElementById('body').innerHTML = '<div id="aceInstance"></div>';
    document.getElementById('menuBarDynamic').innerHTML = '';
    
    document.title = inventoryObject.name;
    document.getElementById('bodyTitle').innerHTML = inventoryObject.type.toUpperCase() + ': ' + inventoryObject.name;
    $('.nav-tabs a[href="#body"]').tab('show');
    
    initAttributes();
    addAttributeText('UUID', 'objuuid');
    addAttributeTextBox('Name', 'name');
    addAttributeTextArea('Description', 'description');
    addAttributeTextBox('Minutes', 'minutes');
    addAttributeTextBox('Hours', 'hours');
    addAttributeTextBox('Day of Month', 'dayofmonth');
    addAttributeTextBox('Day of Week', 'dayofweek');
    addAttributeTextBox('Year', 'year');
    addAttributeCheckBox('Enabled', 'enabled');

    var editor = new ace.edit(document.getElementById('aceInstance'));
    
    //editor.setTheme("ace/theme/twilight");
    editor.session.setMode("ace/mode/python");
    editor.setValue(inventoryObject['body']);
    editor.selection.moveTo(0, 0);
    editor['inventoryObject'] = inventoryObject;
                                        
    editor.on('change', function(e, f) {
        f.inventoryObject['body'] = f.getValue();
        f.inventoryObject['changed'] = true;
    });
    
    loadRequiresGrid();
    loadProvidesGrid();
}

var loadAndEditSchedule = function(objuuid) {
    document.getElementById('body').innerHTML = '';
    document.getElementById('menuBarDynamic').innerHTML = '';
    
    $.ajax({
        'url' : 'inventory/ajax_get_object',
        'dataType' : 'json',
        'method': 'POST',
        'data' : {'objuuid' : objuuid},
        'success' : function(resp) {
            inventoryObject = resp;
            editSchedule();
            expandToNode(inventoryObject.objuuid);
        }
    });
}