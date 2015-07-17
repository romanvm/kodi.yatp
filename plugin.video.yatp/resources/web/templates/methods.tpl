<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Available JSON-RPC Methods</title>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css">
    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
</head>
<body>
<div style="padding:20px">
    <h1>Available JSON-RPC methods</h1>
    <p>
        <table class="table table-bordered">
            <tr>
                <th>Method</th>
                <th>Description</th>
            </tr>
            % for method, doc in zip(methods, docs):
            <tr>
                <td>{{method}}</td>
                <td>{{!doc}}</td>
            </tr>
            % end
        </table>
    </p>
</div>
</body>
</html>
