/*
 * Copyright (c) 2023. PortSwigger Ltd. All rights reserved.
 *
 * This code may be used to extend the functionality of Burp Suite Community Edition
 * and Burp Suite Professional, provided that this usage does not violate the
 * license terms for those products.
 */

package io.github.cyal1.bcryptmontoya;

import burp.api.montoya.core.Annotations;
import burp.api.montoya.http.handler.*;
import burp.api.montoya.http.message.requests.HttpRequest;
import burp.api.montoya.http.message.responses.HttpResponse;

import java.util.ArrayList;

public class MyHttpHandler implements HttpHandler
{
    @Override
    public RequestToBeSentAction handleHttpRequestToBeSent(HttpRequestToBeSent httpRequestToBeSent) {

        if(BcryptMontoya.status == BcryptMontoya.STATUS.STOP || !BcryptMontoya.py_functions.containsKey("handleRequest")){
            return RequestToBeSentAction.continueWith(httpRequestToBeSent);
        }

        // url prefix allowed
        if(!BcryptMontoya.isPrefixAllowed(httpRequestToBeSent.url())){
            return RequestToBeSentAction.continueWith(httpRequestToBeSent);
        }

        ArrayList<Object> array = BcryptMontoya.invokePyRequest(httpRequestToBeSent, httpRequestToBeSent.annotations(), "handleRequest");
        return RequestToBeSentAction.continueWith((HttpRequest) array.get(0), (Annotations) array.get(1));
    }
    @Override
    public ResponseReceivedAction handleHttpResponseReceived(HttpResponseReceived httpResponseReceived) {

        if(BcryptMontoya.status == BcryptMontoya.STATUS.STOP || !BcryptMontoya.py_functions.containsKey("handleResponse")){
            return ResponseReceivedAction.continueWith(httpResponseReceived);
        }

        // url prefix allowed
        if(!BcryptMontoya.isPrefixAllowed(httpResponseReceived.initiatingRequest().url())){
            return ResponseReceivedAction.continueWith(httpResponseReceived);
        }

        ArrayList<Object> array = BcryptMontoya.invokePyResponse(httpResponseReceived, httpResponseReceived.annotations(), "handleResponse");
        return ResponseReceivedAction.continueWith((HttpResponse) array.get(0), (Annotations) array.get(1));
    }
}
