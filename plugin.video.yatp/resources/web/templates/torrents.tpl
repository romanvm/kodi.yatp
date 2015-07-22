<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Torrents</title>
    <link rel="stylesheet" type="text/css" href="/static/easyui/themes/default/easyui.css">
    <link rel="stylesheet" type="text/css" href="/static/easyui/themes/icon.css">
    <link rel="stylesheet" type="text/css" href="/static/easyui/demo.css">
    <script src="/static/js/jquery-1.6.4.min.js"></script>
    <script src="/static/easyui/jquery.easyui.min.js"></script>
    <script src="/static/easyui/plugins/jquery.datagrid.js"></script>
    <!-- Custom css and js -->
    <link rel="stylesheet" type="text/css" href="/static/css/torrents.css">
    <script src="/static/js/torrents.js"></script>
</head>
<body>
    <div>
        <table id="torrents" title=""></table>
    </div>
    <div id="toolbar">
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-torrent-add" plain="true" onclick="$('#add_torrent_dlg').dialog('open')">Add .torrent file</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-link-add" plain="true" onclick="$('#add_link_dlg').dialog('open')">Add torrent link</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-pause" plain="true" onclick="pause_torrent()">Pause</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-resume" plain="true" onclick="resume_torrent()">Resume</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-pause-red" plain="true" onclick="pause_all()">Pause all</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-resume-red" plain="true" onclick="resume_all()">Resume all</a>
        <a href="javascript:void(0)" class="easyui-linkbutton"
           iconCls="icon-delete" plain="true" onclick="confirm_remove_torrent()">Delete torrent</a>
    </div>
    <div id="add_torrent_dlg" style="padding:10px">
        <form id="add_torr_file_form" action="add-torrent-file" method="post" enctype="multipart/form-data">
            <input id="torr_path" name="torrent_file" class="easyui-filebox" style="width:100%;height:26px",
                    data-options="prompt:'Select a .torrent file'">
        </form>
    </div>
    <div id="add_link_dlg" style="padding:10px">
        <input id="torrent_link" class="easyui-textbox" style="width:100%;height:26px"
               data-options="prompt:'Insert a .torrent file URL or a magnet link here'">
    </div>
    <div id="remove_torrent_dlg" style="padding:10px">
        <p><strong>Are you sure you want to delete the torrent?</strong></p>
        <p><input id="delete_files" type="checkbox" name="delete_files" value=""> Also delete files from disc.</p>
        <p><strong>WARNING:</strong> The files will be deleted permanently!</p>
    </div>
</body>
</html>
