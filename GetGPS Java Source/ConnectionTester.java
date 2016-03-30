/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gpsa;

import java.net.InetSocketAddress;
import java.net.Socket;

/**
 *
 * @author Piotr Tekieli <p.s.tekieli@student.tudelft.nl>
 */
    public class ConnectionTester {
       protected boolean TestRemotePort(String gpsshare_ipaddress, int gpsshare_port, int timeout) {
        try {
            Socket testsocket = new Socket();
            testsocket.connect(new InetSocketAddress(gpsshare_ipaddress, gpsshare_port), timeout);
            testsocket.close();
            return true;
        } catch (Exception port_ex) {
            System.out.println("Error while testing remote port: " + port_ex);
            return false;
        }
    }
       
    /* Reused from (source) : http://stackoverflow.com/a/5240291 */
    protected boolean validIP (String ip) {
        try {
            if ( ip == null || ip.isEmpty() ) {
                return false;
            }
            String[] parts = ip.split( "\\." );
            if ( parts.length != 4 ) {
                return false;
            }
            for ( String s : parts ) {
                int i = Integer.parseInt( s );
                if ( (i < 0) || (i > 255) ) {
                    return false;
                }
            }
            if ( ip.endsWith(".") ) {
                return false;
            }
            
            return true;
        } catch (NumberFormatException nfe) {
            System.out.println("Stage 1 error [IPV4_FORMAT]: " + nfe);
            return false;
        }
    }
    
    protected boolean validPort(String portToparse) {
        try {
            int ParsedPort = Integer.parseInt(portToparse);
            if ( (ParsedPort < 0) || (ParsedPort > 65535) ) 
                return false;              
            return true;
        }
        catch (NumberFormatException nfe) {
            System.out.println("Stage 1 error [PORT_FORMAT]: " + nfe);
            return false;
        }
    } 
}
