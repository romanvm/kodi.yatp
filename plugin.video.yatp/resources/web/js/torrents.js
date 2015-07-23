// Start function declaration
function pause_torrents()
{
    var torrents = $('#torrents').datagrid('getSelections');
    if (torrents.length > 0)
    {
        var hashes = '["' + torrents[0].info_hash;
        for (i=1; i<torrents.length; i++)
        {
            hashes += '","' + torrents[i].info_hash
        }
        hashes += '"]'
        $.ajax({type:'POST',
                url:'/json-rpc',
                data:'{"method":"pause_group", "params":[' + hashes + ']}',
                contentType:'application/json',
                dataType:'json'
        }); // end ajax
    } // end if
} // end pause_torrents

function resume_torrents()
{
    var torrents = $('#torrents').datagrid('getSelections');
    if (torrents.length > 0)
    {
        var hashes = '["' + torrents[0].info_hash;
        for (i=1; i<torrents.length; i++)
        {
            hashes += '","' + torrents[i].info_hash
        }
        hashes += '"]'
        $.ajax({type:'POST',
                url:'/json-rpc',
                data:'{"method":"resume_group", "params":[' + hashes + ']}',
                contentType:'application/json',
                dataType:'json'
        }); // end ajax
    } // end if
} // end resume_torrent

function confirm_remove_torrents()
{
    if ($('#torrents').datagrid('getSelected') != null)
    {
        $('#remove_torrent_dlg').dialog('open');
    } // end if
} // end confirm remove torrents

function remove_torrents()
{
    var torrents = $('#torrents').datagrid('getSelections');
    var delete_files = $('#delete_files').prop('checked');
    var hashes = '["' + torrents[0].info_hash;
    for (i=1; i<torrents.length; i++)
    {
        hashes += '","' + torrents[i].info_hash
    }
    hashes += '"]'
    $.ajax({type:'POST',
            url:'/json-rpc',
            data:'{"method":"remove_group", "params":[' + hashes + ',' + delete_files + ']}',
            contentType:'application/json',
            dataType:'json'
    }); // end ajax
    $('#delete_files').prop('checked',false);
    $('#remove_torrent_dlg').dialog('close');
    $('#torrents').datagrid('clearSelections')
} // end remove_torrent

function add_torrent_file()
{
    var ext = $('#torr_path').filebox('getValue').split('.').pop();
    if (ext == 'torrent')
    {
        $('#add_torr_file_form').form('submit');
        $('#torr_path').filebox('clear');
        $('#file_sub_path').textbox('clear');
        $('#add_torrent_dlg').dialog('close');
    }
    else
    {
        $.messager.alert('Error','Invalid file selected!','error');
    }
}

function add_torrent_link()
{
    var torrent_link = $('#torrent_link').textbox('getValue');
    if (torrent_link && (torrent_link.slice(0, 7) == 'magnet:' || torrent_link.slice(0, 4) == 'http'))
    {
        $('#add_torr_link_form').form('submit');
        $('#torrent_link').textbox('clear');
        $('#link_sub_path').textbox('clear');
        $('#add_link_dlg').dialog('close');
    }
    else
    {
        $.messager.alert('Error','Invalid torrent link!','error');
    } // end if
} // end add_magnet

function pause_all()
{
    $.ajax({
            type:'POST',
            url:'/json-rpc',
            data:'{"method": "pause_all"}',
            contentType:'application/json',
            dataType:'json'
        }); // end ajax
} // end pause_all

function resume_all()
{
    $.ajax({
            type:'POST',
            url:'/json-rpc',
            data:'{"method": "resume_all"}',
            contentType:'application/json',
            dataType:'json'
        }); // end ajax
} // end resume_all

function grid_refresh()
{
    $('#torrents').datagrid('reload'); // reload grid
    $('#torrents').datagrid('loaded'); // hide 'loading' message
} // end grid_refresh
// Start JQuery document_ready
$(function()
{
    $('#torrents').attr('title','Torrents on ' + window.location.host);
    $('#torrents').datagrid({
        singleSelect:false,
        ctrlSelect:true,
        url:'torrents-json',
        method:'get',
        idField:'info_hash',
        rownumbers:true,
        loadMsg: 'Loading torrents data...',
        remoteSort:false,
        toolbar:'#toolbar',
        onLoadSuccess: function()
        {
            setTimeout(grid_refresh, 2000);
        },
        onLoadError: function()
        {
            $.messager.alert('Error!','Unable to load torrents data!','error');
        },
        columns:[[
            {field:'name',title:'Torrent Name',sortable:true,width:400},
            {field:'size',title:'Size (MB)',width:70,align:'right'},
            {field:'state',title:'State',width:100},
            {field:'progress',title:'%',width:35,align:'right'},
            {field:'dl_speed',title:'DL (KB/s)',width:70,align:'right'},
            {field:'ul_speed',title:'UL (KB/s)',width:70,align:'right'},
            {field:'total_download',title:'Total DL (MB)',width:90,align:'right'},
            {field:'total_upload',title:'Total UL (MB)',width:90,align:'right'},
            {field:'num_seeds',title:'Seeds',width:50,align:'right'},
            {field:'num_peers',title:'Peers',width:50,align:'right'},
            {field:'added_time',title:'Added on',sortable:true,width:150},
            {field:'completed_time',title:'Completed on',width:150},
            {field:'info_hash',title:'Hash',width:300}
        ]] // end columns
    }); // end datagrid
    $('#torrents').datagrid('sort', 'added_time');
    $('#add_torrent_dlg').dialog({
        title: 'Add .torrent file',
        iconCls: 'icon-torrent-add',
        width: 450,
        height: 170,
        closed: true,
        modal: true,
        buttons: [{
            text: 'Add',
            iconCls: 'icon-ok',
            handler: function()
                {
                    add_torrent_file();
                } // end function
            }, // end button
            {
            text: 'Cancel',
            handler: function()
                {
                    $('#torr_path').filebox('clear');
                    $('#file_sub_path').textbox('clear');
                    $('#add_torrent_dlg').dialog('close');
                } // end function
            } // end button
        ] // end buttons
    }); // end dialog
    $('#add_link_dlg').dialog({
        title: 'Add Torrent Link',
        iconCls: 'icon-link-add',
        width: 450,
        height: 170,
        closed: true,
        modal: true,
        buttons: [{
            text: 'Add',
            iconCls: 'icon-ok',
            handler: function()
                {
                    add_torrent_link();
                } // end function
            }, // end button
            {
            text: 'Cancel',
            handler: function()
                {
                    $('#torrent_link').textbox('clear');
                    $('#link_sub_path').textbox('clear');
                    $('#add_link_dlg').dialog('close');
                } // end function
            } // end button
        ] // end buttons
    }); // end dialog
    $('#remove_torrent_dlg').dialog({
        title: 'Confirm delete torrents',
        iconCls: 'icon-delete',
        width: 400,
        height: 180,
        closed: true,
        modal: true,
        buttons: [{
            text: 'Delete',
            iconCls: 'icon-ok',
            handler: function()
                {
                    remove_torrents();
                } // end function
            }, // end button
            {
            text: 'Cancel',
            handler: function()
                {
                    $('#remove_torrent_dlg').dialog('close');
                    $('#delete_files').prop('checked',false);
                } // end function
            } // end button
        ] // end buttons
    }); // end dialog
    $(window).resize(function()
    {
        $('#torrents').datagrid('resize');
        $('#toolbar').panel('resize');
    }
    ); // end window resize
}); // end document_ready
