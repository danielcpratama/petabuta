import pandas as pd
import numpy as np
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium
import time
import webbrowser

# Initialize session state
if 'counter' not in st.session_state:
    st.session_state['counter'] = 1

if 'score' not in st.session_state:
    st.session_state['score'] = 0

if 'mistakes' not in st.session_state:
    st.session_state['mistakes'] = 0

if 'answer' not in st.session_state:
    st.session_state['answer'] = {}


# import required data
@st.cache_data
def get_geom(file):
    gdf = gpd.read_file(file)
    random_numbers = np.random.choice(range(len(gdf)), size=len(gdf), replace=False)
    gdf['sequence'] = random_numbers+1
    gdf = gdf.to_crs(4326)
    return gdf

@st.cache_data
def get_city(file):
    df = pd.read_csv(file)
    return df

gdf = get_geom('geom/ALL_PROVINSI.geojson')
kab_df = get_city('geom/kabupaten.csv')


gdf['status'] = 'not asked'
for i in range(0,len(gdf)): 
    if gdf['sequence'][i] == st.session_state['counter']:
        gdf['status'][i] = 'being asked'
    else:
        gdf['status'][i] = 'not asked'

list_prov = list(gdf['NAMA_PROVINSI'].unique())
list_kab = list(kab_df['NAMA_KAB_KOTA'].unique())

jawaban_PROV = gdf[gdf['status']=='being asked'].NAMA_PROVINSI.iloc[0]
jawaban_IBUKOTA = gdf[gdf['status']=='being asked'].NAMA_IBUKOTA.iloc[0]

# title
st.subheader('Peta Buta Indonesia', divider='grey')

# Next question for skipping
@st.experimental_fragment
def next_question():
    if st.button('Skip question', use_container_width=True):
        # Increment the counter when the button is clicked
        st.session_state['counter'] += 1
        st.rerun()
    return

# share to twitter
def share_to_twitter():
        tweet_text = f"Tes Geografi Umum Peta Buta Ibukota Provinsi Indonesia skor: {st.session_state.score}/76"
        tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"
        webbrowser.open_new_tab(tweet_url)

    

# answer check
@st.experimental_fragment
def answer_check(jawaban, jawabanB):
    if (jawaban == jawaban_PROV) and (jawabanB == jawaban_IBUKOTA):
        st.success('hore dua-duanya benar')
        with st.spinner('pertanyaan selanjutnya..'):
            time.sleep(1)
        st.session_state['answer'][st.session_state['counter']] = 'correct' 
        st.session_state['score'] += 2
        st.session_state['counter'] += 1
        st.rerun()
    
    elif (jawaban == jawaban_PROV) and (jawabanB != jawaban_IBUKOTA):
        st.warning(f'Ups provinsi benar tapi ibukotanya salah, harusnya {jawaban_IBUKOTA}')
        with st.spinner('pertanyaan selanjutnya..'):
            time.sleep(1)
        st.session_state['answer'][st.session_state['counter']] = 'half-correct' 
        st.session_state['score'] += 1
        st.session_state['counter'] += 1
        st.session_state['mistakes'] += 1
        st.rerun()

    elif (jawaban != jawaban_PROV) and (jawabanB == jawaban_IBUKOTA):
        st.warning(f'Ups ibukotanya benar tapi provinsinya salah, harusnya {jawaban_PROV}')
        with st.spinner('pertanyaan selanjutnya..'):
            time.sleep(1)
        st.session_state['answer'][st.session_state['counter']] = 'half-correct' 
        st.session_state['score'] += 1
        st.session_state['counter'] += 1
        st.session_state['mistakes'] += 1
        st.rerun()

    else:
        st.error(f'O ow salah besar! jawabannya Provinsi {jawaban_PROV}, ibukota {jawaban_IBUKOTA}')
        with st.spinner('pertanyaan selanjutnya..'):
            time.sleep(1)
        st.session_state['answer'][st.session_state['counter']] = 'wrong' 
        st.session_state['counter'] += 1
        st.session_state['mistakes'] += 2
        st.rerun()


#--------- MAIN PAGE ---------------------------------------------------
def main():
    # make and display maps
    map = gdf.explore(tiles = None,
                        column = 'status',
                        cmap = 'Set1',
                        categorical = True, 
                        highlight = False,
                        zoom_on_click = True, 
                        style_kwds = {'color' : 'black', 'weight':0.2, 'fillOpacity':100 },
                        tooltip = True, 
                        )

    with st.container(border=False, height=350):
        output = st_folium(map, 
                returned_objects=[], 
                use_container_width=True, 
                height=350,
                )

    # insert answer here
    with st.form(key='jawab', border=False):
        colA, colB = st.columns([1,1])
        with colA:
            jawaban = st.selectbox('Apa nama provinsi berwarna merah?', list_prov)
        with colB:
            jawabanB = st.selectbox('Apa nama ibukotanya?', list_kab)

        if st.form_submit_button('submit jawaban', use_container_width=True, type='primary'):
            answer_check(jawaban, jawabanB)

    # display game status
    colA, colB, colC = st.columns([1,1,1])
    with colA: 
        st.metric('Questions Number: (max:32)', st.session_state['counter'])
    with colB: 
        st.metric('Score: (max=64)', st.session_state['score'])
    with colC: 
        st.metric('Mistakes: (max=6)', st.session_state['mistakes'])

if (st.session_state['counter'] <=38) and (st.session_state['mistakes'] <6) : 
    main()

else: #--------- GAME OVER PAGE ---------------------------------------------------
    fin_df = pd.DataFrame(st.session_state['answer'], index=[0]).T.reset_index()
    fin_df.columns = ['sequence', 'answer']
    fin_gdf = pd.merge(gdf, fin_df, how='left', on='sequence').fillna('unanswered')
    
    #st.write(fin_gdf)
    st.subheader('Game Over')
    # def generate_map(gdf):
    fin_map = fin_gdf.explore(column = 'answer', 
                    cmap='RdYlGn_r',
                    categorical = True,
                    categories = ['correct', 'half-correct', 'unanswered', 'wrong'], 
                    tooltip = ['NAMA_PROVINSI', 'NAMA_IBUKOTA', 'answer'], 
                    tiles=None,
                    zoom_on_click = True,
                    legend = True,
                    style_kwds = {'stroke' : True, 'color': 'black', 'weight':0.2, 'fillOpacity': 90},
                            )
    
    with st.container(height=400):
        st_folium(fin_map, height= 350,
                  use_container_width=True, 
                  returned_objects=[])
    
    
    # display game status
    colA, colB, colC = st.columns([1,1,1])
    with colA: 
        st.metric('Questions Number: (max=38)', st.session_state['counter'])
    with colB: 
        st.metric('Score: (max=76)', st.session_state['score'])
    with colC: 
        st.metric('Mistakes: (max=6)', st.session_state['mistakes'])
    
    
    # replay game
    colA, colB = st.columns([1,1])
    with colA:
        st.write('please donasi Rp 5,000 untuk replay game')
        st.image('image/QRIS_small.jpg', width=200)
    with colB:
        disabled = True
        bayar = st.text_input('4 dijit terakhir referensi pembayaran QRIS', max_chars=4, value='')
        if bayar != '':
            disabled = False
        st.caption('jangan lupa screenshot, copy text dibawah, terus share ke twitter/instagram ya!')
        text = f"Tes Geografi Umum Peta Buta Ibukota Provinsi Indonesia skor: {st.session_state.score}/76 - petabuta.streamlit.app"
        st.code(f'{text}')

        if st.button('replay', use_container_width=True, disabled=disabled, type='primary'):
            st.session_state['counter'] = 1
            st.session_state['score'] = 0
            st.session_state['mistakes'] = 0
            st.rerun()
