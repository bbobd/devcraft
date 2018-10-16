import os
import re
import json
import requests
from operator import itemgetter
from bs4 import BeautifulSoup
from nltk import tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer

'''
str=start
end=end
dtm=datetime
'''
domain="https://www.reddit.com/"
query="search?q=samsung+note+9&sort=new&t=all"
str_dtm="2018-10-07T00:00"
end_dtm="2018-10-11T23:59"
url=domain+query

headers={'User-Agent':'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)1'}
req=requests.get(url,verify=True,headers=headers)
##req=requests.get(url,verify=False,headers=headers)
html=req.text
soup=BeautifulSoup(html,'html.parser')
pst_div_list=soup.find_all('div',attrs={'class':re.compile(' search-result search-result-link +')})

'''
nxt=next
dne=done
flg=flag
pge=page
pst=post
'''
nxt_url=None
dne_flg=False
pge_cnt=0
pst_cnt=0
'''
ttl=total
pos=positive
neg=negative
scr=score
rpl=reply
'''
ttl_pos_scr=0
ttl_neg_scr=0
ttl_rpl_pos_scr=0
ttl_rpl_neg_scr=0
'''
doc=document
snt=sentence
'''
pst_top_list=[]
pst_top_pos_list=[]
pst_top_neg_list=[]
snt_top_pos_list=[]
snt_top_neg_list=[]
ttl_top_pos_list=[]
ttl_top_neg_list=[]

while not dne_flg:
  if nxt_url is not None:
    print('next url is : '+nxt_url)
    req=requests.get(nxt_url,verify=True,headers=headers)
    ##req=requests.get(nxt_url,verify=False,headers=headers)
    html=req.text
    soup=BeautifulSoup(html,'html.parser')
    pst_div_list=soup.find_all('div',attrs={'class':re.compile(' search-result search-result-link +')})
  pge_cnt+=1
  print('now crawling... page '+str(pge_cnt))
  if pst_div_list is not None:
    print(str(pge_cnt)+' page has '+str(len(pst_div_list))+' posts')
    for pst_div in pst_div_list:
      '''get information as below:
      headline
      post_url
      reply_url
      created_datetime
      content
      point_cnt
      reply_cnt
      '''
      dtm_tag=pst_div.find('time')
      dtm=dtm_tag.attrs['datetime']
      if dtm >= str_dtm and dtm <= end_dtm:
        pst_cnt+=1
        print('post number '+str(pst_cnt)+' : created datetime '+dtm)
        '''
        anc=anchor
        ctn=content
        pnt=point
        '''
        pst_anc=pst_div.find('a',attrs={'class':'search-title may-blank'})
        rpl_anc=pst_div.find('a',attrs={'class':'search-comments may-blank'})
        ctn_tag=pst_div.find('div',attrs={'class':'search-result-body'})
        if ctn_tag is not None:
          ctn=ctn_tag.text
        else:
          ctn=pst_anc.text
        '''
        pnt_tag=pst_div.find('span',attrs={'class':'search-score'})##? points
        pnt_scr=pnt_tag.text
        rpl_scr=rpl_tag.text
        ##Todo:split strings##
        '''
        ##sentiment analyze##
        ##begien           ##
        pst_lines=[]
        pst_pos_scr=0
        pst_neg_scr=0
        lines=tokenize.sent_tokenize(ctn)
        sid=SentimentIntensityAnalyzer()
        for line in lines:
          '''
          stm=sentiment
          '''
          stm_scr=sid.polarity_scores(line)
          for k in sorted(stm_scr):
            if k=='pos':
              line_pos_scr=0
              line_pos_scr=round(stm_scr[k],2)*100
              pst_pos_scr+=stm_scr[k]
            if k=='neg':
              line_neg_scr=0
              line_neg_scr=round(stm_scr[k],2)*100
              pst_neg_scr+=stm_scr[k]
          pst_lines.append({'line':line,'pos':int(line_pos_scr),'neg':int(line_neg_scr),'diff':int(line_pos_scr-line_neg_scr)})
        ttl_pos_scr+=pst_pos_scr
        ttl_neg_scr+=pst_neg_scr
        '''
        print(dtm+' positive score: '+str(round(pst_pos_scr,3)))
        print(dtm+' negative score: '+str(round(pst_neg_scr,3)))
        '''
        pst_url=pst_anc.attrs['href']
        
        temp_list=[]
        temp_cnt=0
        temp_list=sorted(pst_lines,key=itemgetter('pos'),reverse=True);
        for item in temp_list:
          if item['diff']>0:
            temp_cnt+=1
            snt_top_pos_list.append(item)
          if temp_cnt==10:
            break
        temp_cnt=0
        temp_list=sorted(pst_lines,key=itemgetter('neg'),reverse=True);
        for item in temp_list:
          if item['diff']<0:
            temp_cnt+=1
            snt_top_neg_list.append(item)
        ##crawling replies##
        ##begin           ##
        sub_req=requests.get(rpl_anc.attrs['href'],verify=True,headers=headers)
        ##sub_req=requests.get(rpl_anc.attrs['href'],verify=False,headers=headers)
        sub_html=sub_req.text
        sub_soup=BeautifulSoup(sub_html,'html.parser')
        '''
        cmt=comment
        '''
        cmt_div_list=sub_soup.find_all('div',attrs={'data-type':'comment'})
        cmt_cnt=0

        rpl_pos_scr=0
        rpl_neg_scr=0
        if cmt_div_list is not None:
          for cmt_div in cmt_div_list:
            cmt=cmt_div.find('div',attrs={'class':'md'})
            cmt_cnt+=1
        ###end             ##
            ##sentiment of comments##
            ##begin                ##
            rpl_lines=[]
            rpl_lines=tokenize.sent_tokenize(cmt.text)
            for line in rpl_lines:
              stm_rpl_scr=sid.polarity_scores(line)
              for k in sorted(stm_rpl_scr):
                if k=='pos':
                  line_pos_scr=0
                  line_pos_scr=round(stm_rpl_scr[k],2)
                  rpl_pos_scr+=line_pos_scr*100
                  ttl_rpl_pos_scr=line_pos_scr
                if k=='neg':
                  line_neg_scr=0
                  line_neg_scr=round(stm_rpl_scr[k],2)
                  rpl_neg_scr+=line_neg_scr*100
                  ttl_rpl_neg_scr=line_neg_scr
            ##end                  ##
        pst_top_list.append({'url':pst_url,'pos':int(pst_pos_scr*100),'neg':int(pst_neg_scr*100),'diff':int((pst_pos_scr-pst_neg_scr)*100),'cmt_cnt':cmt_cnt,'cmt_pos_scr':str(rpl_pos_scr/100),'cmt_neg_scr':str(rpl_neg_scr/100)})

      elif dtm < str_dtm:
        dne_flg=True
        break
    if soup.find_all('a',attrs={'rel':'nofollow next'}) is not None:
      nxt_anc_list=soup.find_all('a',attrs={'rel':'nofollow next'})
      print('nxt_anc cnt: '+str(len(nxt_anc_list)))
      for nxt_anc in nxt_anc_list:
        nxt_url=nxt_anc.get('href')##must get the last nxt_tag.href
      snt_top_pos_list=sorted(snt_top_pos_list,key=itemgetter('pos'),reverse=True)[:10]
      snt_top_neg_list=sorted(snt_top_neg_list,key=itemgetter('pos'),reverse=True)[:10]      
    else:
      dne_flg=True
      print('This is the last page: '+str(pge_cnt))
      break
  else:
    dne_flg=True
    print('post list is not exist (,although url is exist)')
    break
  
  if dne_flg:
    temp_cnt=0
    for pst in sorted(pst_top_list,key=itemgetter('pos'),reverse=True):
      if pst['diff']>0:
        temp_cnt+=1
        pst_top_pos_list.append(pst)
      if temp_cnt==10:
        break
    temp_cnt=0
    for pst in sorted(pst_top_list,key=itemgetter('neg'),reverse=True):
      if pst['diff']<0:
        temp_cnt+=1
        pst_top_neg_list.append(pst)
      if temp_cnt==10:
        break
    print('job is done')
    print()

result=[]
result.append('query         : '+query+'\n')
result.append('start datetime: '+str_dtm+'\n')
result.append('end datetime  : '+end_dtm+'\n')
result.append('\n')

result.append('Total posts count: '+str(pst_cnt)+'\n')
result.append('Total positive score: '+str(round(ttl_pos_scr,2))+'\n')
result.append('Total negative score: '+str(round(ttl_neg_scr,2))+'\n')
result.append('\n')

result.append('Positive top sentences'+'\n')
for item in (sorted(snt_top_pos_list,key=itemgetter('pos'),reverse=True)[:10]):
  result.append(item['line']+'\n')
result.append('\n')

result.append('Nagative top sentences'+'\n')
for item in (sorted(snt_top_neg_list,key=itemgetter('neg'),reverse=True)[:10]):
  result.append(item['line']+'\n')
result.append('\n')

result.append('Positive posts \n')
for pst in pst_top_pos_list:
  result.append(pst['url']+'\n')
  result.append('positive score: '+str(pst['pos']/100)+'| cmt cnt: '+str(pst['cmt_cnt'])+'\n')
  result.append('| cmt positive score: '+pst['cmt_pos_scr']+'| cmt negative score: '+pst['cmt_neg_scr']+'\n')
result.append('\n')

result.append('Negative posts \n')
for pst in pst_top_neg_list:
  result.append(pst['url']+'\n')
  result.append('negative score: '+str(pst['neg']/100)+'| cmt cnt: '+str(pst['cmt_cnt'])+'\n')
  result.append('| cmt positive score: '+pst['cmt_pos_scr']+'| cmt negative score: '+pst['cmt_neg_scr']+'\n')
result.append('\n')

f=open('./result.txt','w',encoding='UTF8')
f.write(''.join(result))
f.close()

header=req.headers
status=req.status_code
is_ok=req.ok
