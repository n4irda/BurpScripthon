# BurpScripthon

 BurpScripthon is a plugin for BurpSuite that allows the analysis of http requests
and responses,  through python scripts.
#### Note:  
Only work for linux.(Because path implementation; you can make a PR)


### Installation.
Clone this repo with `git clone http://github.com/n4irda.code/BurpScripthon.git`
and load it from BurpSuite.


### Quick Start.
- To use your scripts, you need to put them in $HOME/.BurpScripthon/scripts folder,
then write the name of your script in BurpScripthon and load it.

- Your scripts must have two functions called `requests` and `response`, 
they both take two arguments called `HttpMessageInfo` and `extension`.
```
    def request(HttpMessageInfo, extension):
        '''
        Process a http request before send it.
        
        arguments:
            HttpMessageInfo: Instance of (burp.IHttpRequestResponse)
            extension: Instance of (BurpScripthon)
            
        return: Message string to put in `Script Out` tab, or None.
        '''
        
    def response(HttpMessageInfo, extension):
        '''
        Process a http response before send it.
        
        arguments:
            HttpMessageInfo: Instance of (burp.IHttpRequestResponse)
            extension: Instance of (BurpScripthon)
            
        return: Message string to put in `Script Out` tab, or None.
        '''
```

- BurpScripthon include a copy of BeautifulSoup4, you can use it in your script with
`import bs4`


### Examples.

See the code in folder scripts for examples..
