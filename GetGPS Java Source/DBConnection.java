/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gpsa;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;

/**
 *
 * @author Piotr Tekieli <p.s.tekieli@student.tudelft.nl>
 */
public class DBConnection {
   
    private Connection toDB = null;
    private String DBPath = "imsicc.db"; //Default path
    
    public DBConnection(String source) {
        SetDBPath(source);
        CreateConnection();
    }
           
    private void CreateConnection() {        
        try {
          Class.forName("org.sqlite.JDBC");
          toDB = DriverManager.getConnection("jdbc:sqlite:" + DBPath);
        } catch ( ClassNotFoundException | SQLException db_ex ) {
          System.err.println( db_ex.getClass().getName() + ": " + db_ex.getMessage() );
          System.exit(110);
        }              
      }
    
    public void CloseConnection() {
        try {            
            toDB.close();
        } catch (SQLException sql_ex) {
            System.out.println("Error closing connection with the database. " + sql_ex);
            System.exit(112);
        }
    }
    
    private void SetDBPath(String path) {
        DBPath = path;
    }
    
    public int UpdateStatement(String sql) {
        try {
            Statement st = toDB.createStatement();            
            int rowcount = st.executeUpdate(sql);            
            st.close();
            return rowcount;
        } catch (SQLException sql_ex) {
            System.out.println("Error while performing I/O operations on the database. " + sql_ex);
            System.exit(111);            
        }
        return 0;
    }
}
