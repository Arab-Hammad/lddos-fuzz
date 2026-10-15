import org.apache.http.ExceptionLogger;
import org.apache.http.HttpException;
import org.apache.http.HttpRequest;
import org.apache.http.HttpRequestInterceptor;
import org.apache.http.HttpResponse;
import org.apache.http.HttpStatus;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.bootstrap.HttpServer;
import org.apache.http.impl.bootstrap.ServerBootstrap;
import org.apache.http.config.SocketConfig;
import org.apache.http.protocol.HttpContext;
import org.apache.http.protocol.HttpRequestHandler;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class VulnerableJavaServer {

    public static void main(String[] args) throws Exception {

        SocketConfig socketConfig = SocketConfig.custom()
                .setSoTimeout(0)
                .setBacklogSize(1)
                .build();

        HttpServer server = ServerBootstrap.bootstrap()
                .setListenerPort(8080)
                .setLocalAddress(java.net.InetAddress.getByName("0.0.0.0"))
                .setSocketConfig(socketConfig)
                .addInterceptorFirst(new HttpRequestInterceptor() {
                    @Override
                    public void process(HttpRequest request, HttpContext context) {
                        System.out.println("\n[LOG] ---> Incoming Request Headers Received!");
                        System.out.println("[LOG] Request Line: " + request.getRequestLine());

                        for (org.apache.http.Header header : request.getAllHeaders()) {
                            System.out.println("[LOG] Header -> " + header.getName() + ": " + header.getValue());
                        }
                    }
                })
                .registerHandler("*", new HttpRequestHandler() {
                    @Override
                    public void handle(HttpRequest request, HttpResponse response, HttpContext context)
                            throws HttpException, IOException {
                        response.setStatusCode(HttpStatus.SC_OK);
                        response.setEntity(new StringEntity(
                                "Vulnerable Java Server Response Active", ContentType.TEXT_PLAIN));
                    }
                })
                .setExceptionLogger(ExceptionLogger.STD_ERR)
                .create();

        System.out.println("=========================================================");
        System.out.println("VULNERABLE APACHE HTTPCORE SERVER ONLINE");
        System.out.println("Address: http://0.0.0.0:8080");
        System.out.println("Status: Configured for low-rate testing environment");
        System.out.println("=========================================================");

        server.start();

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\nGracefully terminating the server process...");
            server.shutdown(5, TimeUnit.SECONDS);
        }));
    }
}
