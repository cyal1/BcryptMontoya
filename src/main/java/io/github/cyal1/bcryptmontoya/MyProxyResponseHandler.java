package io.github.cyal1.bcryptmontoya;

import burp.api.montoya.core.Annotations;
import burp.api.montoya.http.message.responses.HttpResponse;
import burp.api.montoya.proxy.http.InterceptedResponse;
import burp.api.montoya.proxy.http.ProxyResponseHandler;
import burp.api.montoya.proxy.http.ProxyResponseReceivedAction;
import burp.api.montoya.proxy.http.ProxyResponseToBeSentAction;
import java.util.ArrayList;

public class MyProxyResponseHandler implements ProxyResponseHandler {
    BcryptMontoyaTab bcryptMontoyaTab;

    public MyProxyResponseHandler(BcryptMontoyaTab bcryptMontoyaTab) {
        this.bcryptMontoyaTab = bcryptMontoyaTab;
    }

    @Override
    public ProxyResponseReceivedAction handleResponseReceived(InterceptedResponse interceptedResponse) {

//        if(!bcryptMontoyaTab.py_functions.containsKey("handleProxyResponse")){
//            return ProxyResponseReceivedAction.continueWith(interceptedResponse, interceptedResponse.annotations());
//        }

        // url prefix allowed
        if(!bcryptMontoyaTab.isPrefixAllowed(interceptedResponse.initiatingRequest().url())){
            return ProxyResponseReceivedAction.continueWith(interceptedResponse, interceptedResponse.annotations());
        }
        try {
            ArrayList<Object> array = bcryptMontoyaTab.invokePyResponse(interceptedResponse, interceptedResponse.annotations(), "handleProxyResponse");
            return ProxyResponseReceivedAction.continueWith((HttpResponse) array.get(0), (Annotations) array.get(1));
        }catch (Exception e){
            bcryptMontoyaTab.logTextArea.append(e.getMessage());
        }
        return ProxyResponseReceivedAction.continueWith(interceptedResponse, interceptedResponse.annotations());
    }
    // after intercept
    @Override
    public ProxyResponseToBeSentAction handleResponseToBeSent(InterceptedResponse interceptedResponse) {
        return ProxyResponseToBeSentAction.continueWith(interceptedResponse, interceptedResponse.annotations());
    }
}