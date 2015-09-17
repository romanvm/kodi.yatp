<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Torrents</title>
    <link rel="icon" href="/static/img/folder_torrents.png" type="image/png" sizes="16x16">
    <link rel="icon" href="/static/img/folder_torrents_big.png" type="image/png" sizes="32x32">
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
    <div>
        <p>Use <strong>Ctrl</strong> key + click to select multiple rows.</p>
    </div>
    <div id="toolbar">
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Add .torrent file"
           data-options="position:'right'" iconCls="icon-torrent-add" plain="true"
           onclick="$('#add_torrent_dlg').dialog('open')"></a>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Add torrent link"
           data-options="position:'right'" iconCls="icon-link-add" plain="true"
           onclick="$('#add_link_dlg').dialog('open')"></a>
        <span class="button-sep"></span>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Pause selected torrents"
           data-options="position:'right'" iconCls="icon-pause" plain="true" onclick="pause_torrents()"></a>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Resume selected torrents"
           data-options="position:'right'" iconCls="icon-resume" plain="true" onclick="resume_torrents()"></a>
        <span class="button-sep"></span>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Pause all torrents"
           data-options="position:'right'" iconCls="icon-pause-red" plain="true" onclick="pause_all()"></a>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Resume all torrents"
           data-options="position:'right'" iconCls="icon-resume-red" plain="true" onclick="resume_all()"></a>
        <span class="button-sep"></span>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Restore selected 'finished' downloads"
           data-options="position:'right'" iconCls="icon-restore" plain="true" onclick="restore_downloads()"></a>
        <span class="button-sep"></span>
        <a href="javascript:void(0)" class="easyui-linkbutton easyui-tooltip" title="Delete selected torrents"
           data-options="position:'right'" iconCls="icon-delete" plain="true" onclick="confirm_remove_torrents()"></a>
    </div>
    <div id="add_torrent_dlg" style="padding:10px">
        <form id="add_torr_file_form" action="add-torrent/file" method="post" enctype="multipart/form-data">
            <div style="margin-bottom:20px">
                <input id="torr_path" name="torrent_file" class="easyui-filebox" style="width:100%;height:26px"
                        data-options="prompt:'Select a .torrent file'">
            </div>
            <input id="file_sub_path" name="sub_path" class="easyui-textbox" style="width:100%;height:26px"
                   data-options="prompt:'Sub-folder for downloading'">
        </form>
    </div>
    <div id="add_link_dlg" style="padding:10px">
        <form id="add_torr_link_form" action="add-torrent/link" method="post">
            <div style="margin-bottom:20px">
                <input id="torrent_link" name="torrent_link" class="easyui-textbox" style="width:100%;height:26px"
                       data-options="prompt:'Insert a .torrent file URL or a magnet link here'">
            </div>
            <input id="link_sub_path" name="sub_path" class="easyui-textbox" style="width:100%;height:26px"
                   data-options="prompt:'Sub-folder for downloading'">
        </form>
    </div>
    <div id="remove_torrent_dlg" style="padding:10px">
        <p><strong>Are you sure you want to delete the selected torrents?</strong></p>
        <p><input id="delete_files" type="checkbox" name="delete_files" value=""> Also delete files from disc.</p>
        <p><strong>WARNING:</strong> The files will be deleted permanently!</p>
    </div>
</body>
</html>
