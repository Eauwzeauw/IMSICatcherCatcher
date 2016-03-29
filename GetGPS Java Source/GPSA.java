/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gpsa;

import java.io.*;
import java.net.*;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Scanner;

/**
 *
 * @author Piotr Tekieli <p.s.tekieli@student.tudelft.nl>
 */
public class GPSA {

    private static int gpsshare_port = 0;
    private static String gpsshare_ipaddress = "0.0.0.0";
    private final static int timeout = 15000;
    private static String nmea = "";
    private static double latitude = 0;
    private static String latitudefull = "";
    private static double longitude = 0;
    private static String longitudefull = "";
    private static boolean locked = true;
    
    public static void main(String[] args) {        
        
        ConnectionTester ctr = new ConnectionTester();
        
        System.out.print("Phase 1/3 - Checking the communication Computer <-> GPS Device... ");        
        if ( ctr.validIP(args[0]) != true ) {
            System.out.println("The provided IP address is not valid");
            System.exit(100);
        }
        gpsshare_ipaddress = args[0];
        
        if ( ctr.validPort(args[1]) != true ) {
            System.out.println("The provided PORT number is not valid");
            System.exit(101);
        }
        gpsshare_port = Integer.parseInt(args[1]);
        
        if ( ctr.TestRemotePort(gpsshare_ipaddress, gpsshare_port, timeout) != true) {
            System.out.println("The software was not able to verify the connection. Try again later!");
            System.exit(102);
        }
        System.out.println(" ...Done!");       
        
        System.out.println("Phase 2/3 - Checking the stream properties and getting NMEA data... ");        
        CheckAndGetNMEA();
        System.out.println(" ...Done!");
        
        System.out.println("Phase 3/3 - Saving data to the database... ");           
        DBConnection db = new DBConnection(args[2]);
        String adate = GetDate();       
        int[] counters = new int[4];
        counters[0] = db.UpdateStatement("UPDATE towers SET recordadded='" + adate + "' WHERE nmea IS null;");
        counters[1] = db.UpdateStatement("UPDATE towers SET latitude='" + latitudefull + "' WHERE nmea IS null;");
        counters[2] = db.UpdateStatement("UPDATE towers SET longitude='" + longitudefull + "' WHERE nmea IS null;");
        counters[3] = db.UpdateStatement("UPDATE towers SET nmea='" + nmea + "' WHERE nmea IS null;");
        db.CloseConnection();
        System.out.println(" ...Done!");        
        
        int sum = 0;
        for (int i : counters)
            sum += i;
        System.out.println(sum + " rows updated! - " + counters[0] + " dates " + counters[1] + " latitudes " + counters[2] + " longitudes and " + counters[3] + " nmea stings");        
    }
    
    private static void CheckAndGetNMEA() {        
        try {
            System.out.println("Waiting for synchronization... [5s]");            
            Socket reader = new Socket();
            try {
                Thread.sleep(5000);
            } catch (InterruptedException ex) {
                System.out.println("Error while trying to execute sleep instruction!" + ex);
            }
            reader.connect(new InetSocketAddress(gpsshare_ipaddress, gpsshare_port), timeout);
            BufferedReader in = new BufferedReader(new InputStreamReader(reader.getInputStream()));            
            String inputLine;
            long timer = System.currentTimeMillis();
            long endtimer = timer + 45000;
            System.out.println("Waiting for GPGGA String... [45s]");   
            while ( System.currentTimeMillis() < endtimer && locked) {
                inputLine = in.readLine();
                //System.out.println(inputLine); //For Debugging Purposes
                if(inputLine.startsWith("$GPGGA")) {
                    String delims = "[,]";                                    
                    String[] tokens = inputLine.split(delims); 
                    if (tokens[2].replace(".","") != null && tokens[4].replace(".","") != null) {                        
                        System.out.println("$GPGGA string found : ");
                        System.out.println(inputLine);                       
                        double latitude_p1 = ( Double.parseDouble(tokens[2].substring(0,2)) );
                        double latitude_p2 = ( (Double.parseDouble( ( tokens[2].replace(".","") ).substring(2) ) / Math.pow(10,6)) / 60 );
                        double longitude_p1 = ( Double.parseDouble(tokens[4].substring(2,3)) );                    
                        double longitude_p2 = ( (Double.parseDouble( ( tokens[4].replace(".","") ).substring(3) ) / Math.pow(10,6)) / 60 );  
                        DecimalFormat rounded = new DecimalFormat("##.######");
                        System.out.println("Are the calculated values correct?");
                        System.out.println("Latitude: " + rounded.format( latitude_p1 + latitude_p2 ) + tokens[3] + " Longitude: " + rounded.format( longitude_p1 + longitude_p2 ) + tokens[5]);
                        System.out.print("Press ENTER to continue or CTRL+C to exit ");
                        KeyPressed();
                        nmea = inputLine;
                        latitude = latitude_p1 + latitude_p2;
                        longitude = longitude_p1 + longitude_p2;
                        latitudefull = rounded.format( latitude ) + tokens[3];
                        longitudefull = rounded.format( longitude ) + tokens[5];
                        locked = false;
                    }
                }  
            }
            if (locked != false) {
                System.out.println("Error getting NMEA data. Try again!");
                System.exit(103);
            }
            in.close();
            reader.close();
        } catch (IOException io_ex) {
            System.out.println("Problem with executing BufferReader section... Try again!" + io_ex);
        }
    }
    
    private static String GetDate() {
      Date now = new Date( );
      SimpleDateFormat df = new SimpleDateFormat ("dd.MM.yyyy hh:mm:ss");
      return df.format(now);
    }
    
    private static void KeyPressed() {
        Scanner scan = new Scanner(System.in);
        scan.nextLine();        
    }
}
