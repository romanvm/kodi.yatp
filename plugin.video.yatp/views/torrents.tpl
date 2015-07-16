<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Torrents</title>
    <link rel="stylesheet" type="text/css" href="http://www.jeasyui.com/easyui/themes/default/easyui.css">
    <link rel="stylesheet" type="text/css" href="http://www.jeasyui.com/easyui/themes/icon.css">
    <link rel="stylesheet" type="text/css" href="http://www.jeasyui.com/easyui/demo/demo.css">
    <script src="http://code.jquery.com/jquery-1.6.min.js"></script>
    <script src="http://www.jeasyui.com/easyui/jquery.easyui.min.js"></script>
    <script src="http://www.jeasyui.com/easyui/jquery.edatagrid.js"></script>
    <!-- Custom css and js -->
    <link rel="stylesheet" type="text/css" href="/static/css/torrents.css">
    <script src="/static/js/torrents.js"></script>
</head>
<body>
    <div>
        <table id="torrents" title="Torrents"></table>
    </div>
    <div id="toolbar">
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-magnet-plus" plain="true" onclick="$('#add_magnet_dlg').dialog('open')">Add Magnet Link</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-pause" plain="true" onclick="pause_torrent()">Pause</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-resume" plain="true" onclick="resume_torrent()">Resume</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-delete" plain="true" onclick="confirm_remove_torrent()">Delete</a>
    </div>
    <div id="add_magnet_dlg" style="padding:10px">
        <p>Insert a torrent magnet link in the field below:</p>
        <input id="magnet_text", class="easyui-textbox" style="width:100%;height:26px">
    </div>
    <div id="remove_torrent_dlg" style="padding:10px">
        <p><strong>Are you sure you want to delete the torrent?</strong></p>
        <p><input id="delete_files" type="checkbox" name="delete_files" value=""> Also delete files from disc</p>
        <p><strong>WARNING!</strong> The files will be deleted permanently.</p>
    </div>
</body>
</html>
