package io.github.cyal1.bcryptmontoya;

import com.google.protobuf.*;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;

public class CallFuncClient {
    private final ManagedChannel channel;
    private final CallFuncServiceGrpc.CallFuncServiceBlockingStub blockingStub;
    public CallFuncClient(String host, int port) {
        this.channel = ManagedChannelBuilder.forAddress(host, port)
                .usePlaintext()
                .build();

       this.blockingStub = CallFuncServiceGrpc.newBlockingStub(channel);
    }

    public Object callFunc(String funcName, Object... args){
    //   https://protobuf.dev/reference/protobuf/google.protobuf/#string-value
        Burpextender.Request.Builder requestBuilder = Burpextender.Request.newBuilder().setFuncName(funcName);
        for (Object arg : args) {
            Any param;
            // Determine the type of the argument and set the corresponding value
            if (arg instanceof String) {
                param = Any.pack(StringValue.of((String) arg));
            }else if(arg instanceof Integer) {
                param = Any.pack(Int64Value.newBuilder().setValue((Integer)arg).build());
            }else if (arg instanceof Double) {
                param = Any.pack(DoubleValue.of((double) arg));
            }else if (arg instanceof Boolean) {
                param = Any.pack(BoolValue.newBuilder().setValue((Boolean) arg).build());
            }else if (arg instanceof byte[]) {
                param = Any.pack(BytesValue.newBuilder().setValue(ByteString.copyFrom((byte[])arg)).build());
            }else{
                System.out.println(arg.getClass().getName() + " param type not support, return empty.");
                param = Any.newBuilder().setValue(ByteString.empty()).build();
            }
            requestBuilder.addArgs(param);
        }

        Burpextender.Request request = requestBuilder.build();
        Any result;
        try {
            Burpextender.Response response = blockingStub.callFunc(request);
            result = response.getRes();
            if(result.is(StringValue.class)){
                return result.unpack(StringValue.class).getValue();
            }else if(result.is(Int64Value.class)){
                return result.unpack(Int64Value.class).getValue();
            } else if(result.is(DoubleValue.class)){
                return result.unpack(DoubleValue.class).getValue();
            }else if(result.is(BoolValue.class)){
                return result.unpack(BoolValue.class).getValue();
            }else if(result.is(BytesValue.class)){
                return result.unpack(BytesValue.class).getValue();
            }else{
                throw new RuntimeException("unexcept type returned, only allowed StringValue,Int64Value,DoubleValue,BoolValue,BytesValue");
            }
        } catch (Exception e){
            BcryptMontoya.Api.logging().logToError(e.getMessage());
            throw new RuntimeException(e.getMessage());
        }
    }

    public void shutdown() {
        channel.shutdown();
    }

//    public static void main(String[] args) {
//        CallFuncClient client = new CallFuncClient("localhost",30051); // Replace with the appropriate address and port
//        Object a = client.callFunc("test", 1, 1.1111, "test", true, new Long("111"));
//        assert a != null;
//        System.out.println(a);
//        System.out.println(((String)a).length());
//        System.out.println(a.getClass().getName());
//        client.shutdown();
//    }
}
