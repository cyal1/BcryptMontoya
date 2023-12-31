package io.github.cyal1.bcryptmontoya;

import burp.api.montoya.core.Annotations;
import burp.api.montoya.http.message.responses.HttpResponse;
import burp.api.montoya.proxy.http.InterceptedResponse;
import burp.api.montoya.proxy.http.ProxyResponseHandler;
import burp.api.montoya.proxy.http.ProxyResponseReceivedAction;
import burp.api.montoya.proxy.http.ProxyResponseToBeSentAction;
import java.util.ArrayList;

public class MyProxyResponseHandler implements ProxyResponseHandler {

    @Override
    public ProxyResponseReceivedAction handleResponseReceived(InterceptedResponse interceptedResponse) {

        if(BcryptMontoya.status == BcryptMontoya.STATUS.STOP || !BcryptMontoya.py_functions.containsKey("handleProxyResponse")){
            return ProxyResponseReceivedAction.continueWith(interceptedResponse);
        }

        // url prefix allowed
        if(!BcryptMontoya.isPrefixAllowed(interceptedResponse.initiatingRequest().url())){
            return ProxyResponseReceivedAction.continueWith(interceptedResponse);
        }

        ArrayList<Object> array = BcryptMontoya.invokePyResponse(interceptedResponse, interceptedResponse.annotations(), "handleProxyResponse");
        return ProxyResponseReceivedAction.continueWith((HttpResponse) array.get(0), (Annotations) array.get(1));
    }
    // after intercept
    @Override
    public ProxyResponseToBeSentAction handleResponseToBeSent(InterceptedResponse interceptedResponse) {
        return ProxyResponseToBeSentAction.continueWith(interceptedResponse);
    }
}