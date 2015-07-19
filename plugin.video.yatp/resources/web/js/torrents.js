function pause_torrent()
{
    var row = $('#torrents').datagrid('getSelected');
    if (row != null)
    {
        $.ajax({type:'POST',
                url:'/json-rpc',
                data:'{"method":"pause_torrent", "params":["' + row.info_hash + '"]}',
                contentType:'application/json',
                dataType:'json'
        }); // end ajax
    } // end if
} // end pause_torrent

function resume_torrent()
{
    var row = $('#torrents').datagrid('getSelected');
    if (row != null)
    {
        $.ajax({type:'POST',
                url:'/json-rpc',
                data:'{"method":"resume_torrent", "params":["' + row.info_hash + '"]}',
                contentType:'application/json',
                dataType:'json'
        }); // end ajax
    } // end if
} // end resume_torrent

function confirm_remove_torrent()
{
    if ($('#torrents').datagrid('getSelected') != null)
    {
        $('#remove_torrent_dlg').dialog('open');
    } // end if
} // end confirm remove torrent

function remove_torrent()
{
    var row = $('#torrents').datagrid('getSelected');
    var delete_files = $('#delete_files').prop('checked');
    $.ajax({
        type:'POST',
        url:'/json-rpc',
        data:'{"method":"remove_torrent", "params":["' + row.info_hash + '",' + delete_files + ']}',
        contentType:'application/json',
        dataType:'json'
    }); // end ajax
    $('#delete_files').prop('checked',false);
    $('#remove_torrent_dlg').dialog('close');
    $('#torrents').datagrid('clearSelections')
} // end remove_torrent

function add_magnet()
{
    var magnet_link = $('#magnet_text').textbox('getValue');
    if (magnet_link && magnet_link.slice(0, 7) == 'magnet:')
    {
        $.ajax({
            type:'POST',
            url:'/json-rpc',
            data:'{"method": "add_torrent", "params":["' + magnet_link + '", "", false]}',
            contentType:'application/json',
            dataType:'json'
        }); // end ajax
        $('#magnet_text').textbox('clear');
        $('#add_magnet_dlg').dialog('close');
    }
    else
    {
        $.messager.alert('Error','Invalid magnet link!','error');
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
    setTimeout(grid_refresh, 2000); // schedule next refresh after 2s
} // end grid_refresh

$(function()
{
    $('#torrents').datagrid({
        singleSelect:true,
        url:'torrents-json',
        method:'get',
        idField:'info_hash',
        rownumbers:true,
        loadMsg: 'Loading torrents data...',
        remoteSort:false,
        toolbar:'#toolbar',
        columns:[[
            {field:'name',title:'Torrent Name',sortable:true,width:400},
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
            {field:'info_hash',title:'Hash',width:350}
        ]] // end columns
    }); // end datagrid
    $('#torrents').datagrid('sort', 'added_time');
    $('#add_magnet_dlg').dialog({
        title: 'Add Magnet Link',
        iconCls: 'icon-magnet-plus',
        width: 500,
        height: 180,
        closed: true,
        modal: true,
        buttons: [{
            text: 'Add',
            iconCls: 'icon-ok',
            handler: function()
                {
                    add_magnet();
                }
            }, // end button
            {
            text: 'Cancel',
            handler: function()
                {
                    $('#add_magnet_dlg').dialog('close');
                } // end function
            } // end button
        ] // end buttons
    }); // end dialog
    $('#remove_torrent_dlg').dialog({
        title: 'Confirm Delete',
        iconCls: 'icon-delete',
        width: 380,
        height: 200,
        closed: true,
        modal: true,
        buttons: [{
            text: 'Delete',
            iconCls: 'icon-ok',
            handler: function()
                {
                    remove_torrent();
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
    grid_refresh();
}); // end document_ready
