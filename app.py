
import streamlit as st
import html
import pandas as pd
import altair as alt
from datetime import date

st.set_page_config(page_title='Project Status Dashboard', layout='wide')

TASK_STATUSES=['Not Started','In Progress','Done','On Hold']
PROJECT_STATUSES=['Planning','In Progress','Completed']
TEST_COLS=["Total TC's",'Executed','Passed','Failed','Blocked','Pending']
SEVERITIES=['Critical','High','Medium','Low']
BUG_COLS=['Total','Open','In Progress','Fixed','Closed','Rejected','Reopen','Not a bug']
RISK_STATUSES=['Open','Closed']

# Dashboard colors (validated for color-blind safety; text always stays in ink colors)
NAVY='#1e3a5f'
INK='#0b0b0b'
INK_2='#52514e'
GRID='#e1e0d9'
STATUS_COLORS={'Planning':'#2a78d6','In Progress':'#eb6834','Completed':'#1baf7a'}
STATUS_ICONS={'Planning':'📝','In Progress':'🔄','Completed':'✅'}
BUG_COLOR='#d03b3b'
RISK_COLOR='#ec835a'

CSS='''
<style>
.block-container{padding-top:3.5rem}
[data-testid="stSidebar"]{background:#1e3a5f}
[data-testid="stSidebar"] *{color:#ffffff !important}
.banner{background:#1e3a5f;border-bottom:4px solid #2a78d6;border-radius:8px;padding:16px 24px;margin-bottom:18px}
.banner h1{color:#ffffff;font-size:1.7rem;margin:0;padding:0}
.banner p{color:#cde2fb;font-style:italic;margin:2px 0 0 0}
[class*="st-key-kpi_"] button{background:#ffffff;border:1px solid rgba(11,11,11,0.10);border-radius:8px;
     padding:12px 16px;min-height:92px;justify-content:flex-start;text-align:left;
     box-shadow:0 1px 3px rgba(11,11,11,0.06);transition:box-shadow .15s,transform .15s}
[class*="st-key-kpi_"] button:hover{box-shadow:0 4px 12px rgba(11,11,11,0.15);transform:translateY(-2px);border-color:rgba(11,11,11,0.10)}
[class*="st-key-kpi_"] button p{color:#0b0b0b;font-size:2rem;font-weight:700;line-height:1.2}
[class*="st-key-kpi_"] button p::before{display:block;color:#52514e;font-size:0.85rem;font-weight:600;margin-bottom:2px}
.detail-title{border-left:6px solid var(--accent);background:#ffffff;border-radius:8px;padding:10px 16px;
     margin:8px 0 16px 0;font-size:1.4rem;font-weight:700;color:#0b0b0b;box-shadow:0 1px 3px rgba(11,11,11,0.06)}
.summary-wrap{overflow-x:auto;border:1px solid rgba(11,11,11,0.10);border-radius:8px;background:#ffffff}
table.summary{width:100%;border-collapse:collapse;font-size:0.9rem}
table.summary th{background:#1e3a5f;color:#ffffff;font-weight:600;padding:8px 10px;text-align:center;line-height:1.25}
table.summary td{padding:8px 10px;text-align:center;border-top:1px solid #e1e0d9;color:#0b0b0b;white-space:nowrap}
table.summary tbody tr:nth-child(even){background:#f4f6f9}
table.summary td:nth-child(-n+3){text-align:left}
.st-badge{border-radius:10px;padding:2px 10px;font-weight:600}
.dot{display:inline-block;width:14px;height:14px;border-radius:50%;vertical-align:middle}
.blocked{color:#d03b3b;font-weight:700}
.ok{color:#006300}
.legend{color:#52514e;font-size:0.8rem;margin-top:6px}
.stTabs [data-baseweb="tab"] p{font-size:1.05rem;font-weight:600}
.detail-title span{color:#52514e;font-weight:600;margin-left:8px}
</style>
'''

def banner(title,subtitle=''):
    st.markdown(f'<div class="banner"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)

def kpi_button(col,key,label,value,accent,icon):
    # A clickable card: the button shows the value, CSS adds the colored edge and the label above it
    k=f'kpi_{key}'.replace(' ','_')
    col.markdown(
        f'<style>.st-key-{k} button{{border-left:6px solid {accent} !important}}'
        f'.st-key-{k} button p::before{{content:"{icon} {label}"}}</style>',unsafe_allow_html=True)
    return col.button(str(value),key=k,width='stretch')

def hbar(data,cat,val,title,color):
    # Horizontal bar with value labels at the bar end; category names on the axis carry identity
    top=max(1,float(data[val].max()))*1.15
    base=alt.Chart(data).encode(
        y=alt.Y(f'{cat}:N',sort=None,title=None,scale=alt.Scale(paddingInner=0.35,paddingOuter=0.2),
                axis=alt.Axis(labelColor=INK_2,labelFontSize=12,ticks=False,domainColor=GRID,labelLimit=180,labelOverlap=False)),
        x=alt.X(f'{val}:Q',title=None,scale=alt.Scale(domain=[0,top]),axis=None),
    )
    bars=base.mark_bar(cornerRadiusEnd=4,size=18,color=color).encode(tooltip=[f'{cat}:N',f'{val}:Q'])
    labels=base.mark_text(align='left',dx=5,color=INK_2,fontSize=12).encode(text=f'{val}:Q')
    chart=(bars+labels).properties(height=alt.Step(34),title=alt.Title(title,anchor='start',color=INK,fontSize=14))
    return chart.configure_view(stroke=None)

def status_donut(df):
    # Projects by status; legend + slice labels carry identity, not color alone
    data=pd.DataFrame({'Status':PROJECT_STATUSES,'Projects':[int((df['OverallStatus']==s).sum()) for s in PROJECT_STATUSES]})
    data=data[data['Projects']>0]
    data['Label']=data['Status']+': '+data['Projects'].astype(str)
    color=alt.Color('Status:N',scale=alt.Scale(domain=list(STATUS_COLORS),range=list(STATUS_COLORS.values())),
                    legend=alt.Legend(title=None,orient='right',labelColor=INK_2,labelFontSize=13,symbolType='circle'))
    base=alt.Chart(data).encode(theta=alt.Theta('Projects:Q',stack=True),color=color,
                                tooltip=['Status:N','Projects:Q'])
    arcs=base.mark_arc(innerRadius=55,outerRadius=100,stroke='#ffffff',strokeWidth=2)
    labels=base.mark_text(radius=125,fontSize=13).encode(text='Label:N',color=alt.value(INK_2))
    total=alt.Chart(pd.DataFrame({'t':[f'{len(df)} Projects']})).mark_text(fontSize=16,fontWeight='bold',color=INK).encode(text='t:N')
    chart=(arcs+labels+total).properties(height=330,padding={'top':12,'left':5,'right':5,'bottom':5},title=alt.Title('Projects by Status',anchor='start',color=INK,fontSize=14))
    return chart.configure_view(stroke=None)

def tint_status(v):
    c=STATUS_COLORS.get(v)
    return f'background-color:{c}26;color:{INK};font-weight:600' if c else ''

DEFAULT_TASKS=[
    'Preprod databases access requests are raised',
    'Analyzing requirements',
    'Creation of test cases',
    'Informal Testing- round 1',
    'Informal Testing- round 2',
    'Formal Testing',
    'Test Case review (TLD)',
]

def default_tasks(owner=''):
    n=len(DEFAULT_TASKS)
    return pd.DataFrame({
        'Task':pd.Series(DEFAULT_TASKS,dtype='str'),
        'Status':pd.Series(['Not Started']*n,dtype='str'),
        'Owner':pd.Series([owner]*n,dtype='str'),
        'Start Date':pd.Series([pd.NaT]*n,dtype='datetime64[ns]'),
        'End Date':pd.Series([pd.NaT]*n,dtype='datetime64[ns]'),
        '% Complete':pd.Series([0]*n,dtype='int'),
        'Comments':pd.Series(['']*n,dtype='str'),
    })

def empty_tests():
    return pd.DataFrame(0,index=['Informal','Formal'],columns=TEST_COLS)

def empty_bugs():
    return pd.DataFrame(0,index=SEVERITIES,columns=BUG_COLS)

def empty_risks():
    return pd.DataFrame({
        'Sr No':pd.Series(dtype='int'),
        'Risk Detail':pd.Series(dtype='str'),
        'Status':pd.Series(dtype='str'),
    })

def with_total_row(bugs):
    out=bugs.copy()
    out.loc['Total']=bugs.sum()
    return out

if 'projects' not in st.session_state:
    st.session_state.projects = pd.DataFrame(columns=[
        'Manager','Project','Owner','OverallStatus','Comments'
    ])

if 'updates' not in st.session_state:
    st.session_state.updates = pd.DataFrame(columns=[
        'Date','Project','Owner','Status','Comments'
    ])

# Per-project report tables, keyed by project name
if 'reports' not in st.session_state:
    st.session_state.reports={}

st.markdown(CSS,unsafe_allow_html=True)

st.sidebar.title('📊 Menu')
page=st.sidebar.radio('Menu', ['Create Project','Daily Update','Dashboard'],label_visibility='collapsed')
if page!='Dashboard':
    st.session_state.pop('dash_view',None)

if page=='Create Project':
    banner('Create Project','Set up a new project and its owner')
    with st.form('create_project'):
        manager=st.text_input('Manager Name')
        project=st.text_input('Project Name')
        owner=st.text_input('Project Owner')
        submit=st.form_submit_button('Create Project')
        if submit and project:
            if project in st.session_state.projects['Project'].tolist():
                st.error('A project with this name already exists.')
            else:
                st.session_state.projects.loc[len(st.session_state.projects)] = [manager,project,owner,'Planning','New Project']
                st.session_state.reports[project]={'tasks':default_tasks(owner),'tests':empty_tests(),'bugs':empty_bugs(),'risks':empty_risks()}
                st.success('Project Created Successfully')

elif page=='Daily Update':
    banner('Owner Daily Status Update','Status, Task Tracker, Test Execution, Bugs & Risks')

    projects=st.session_state.projects['Project'].tolist()

    if not projects:
        st.warning('Create a project first.')
    else:
        project=st.selectbox('Select Project',projects)
        report=st.session_state.reports[project]

        tab1,tab2,tab3,tab4,tab5=st.tabs(['Daily Status','Task Tracker','Test Execution Summary','Bug Bifurcation','Risk'])

        with tab1:
            status=st.selectbox('Overall Status',PROJECT_STATUSES,key=f'status_{project}')
            comments=st.text_area('Comments',key=f'comments_{project}')

        with tab2:
            st.caption('Task Tracker & Risk Overview — standard tasks are pre-filled; use + at the bottom to add more')
            tasks=st.data_editor(
                report['tasks'],key=f'tasks_{project}',num_rows='dynamic',width='stretch',hide_index=True,
                column_config={
                    'Status':st.column_config.SelectboxColumn(options=TASK_STATUSES),
                    'Start Date':st.column_config.DateColumn(format='DD-MMM'),
                    'End Date':st.column_config.DateColumn(format='DD-MMM'),
                    '% Complete':st.column_config.NumberColumn(min_value=0,max_value=100,format='%d%%'),
                },
            )

        with tab3:
            st.caption('Test Progress — Informal and Formal test execution')
            tests=st.data_editor(
                report['tests'],key=f'tests_{project}',width='stretch',
                column_config={c:st.column_config.NumberColumn(min_value=0,step=1) for c in TEST_COLS},
            )

        with tab4:
            st.caption('Bug count by severity — Total row is calculated automatically')
            bugs=st.data_editor(
                report['bugs'],key=f'bugs_{project}',width='stretch',
                column_config={c:st.column_config.NumberColumn(min_value=0,step=1) for c in BUG_COLS},
            )
            st.dataframe(with_total_row(bugs).loc[['Total']],width='stretch')

        with tab5:
            st.caption('Risk register — use + at the bottom to add a risk; Sr No is filled in on save')
            risks=st.data_editor(
                report['risks'],key=f'risks_{project}',num_rows='dynamic',width='stretch',hide_index=True,
                column_config={
                    'Sr No':st.column_config.NumberColumn(disabled=True),
                    'Risk Detail':st.column_config.TextColumn(width='large'),
                    'Status':st.column_config.SelectboxColumn(options=RISK_STATUSES,default='Open'),
                },
            )

        if st.button('Save Update',type='primary'):
            risks=risks.reset_index(drop=True)
            risks['Sr No']=range(1,len(risks)+1)
            st.session_state.reports[project]={'tasks':tasks,'tests':tests,'bugs':bugs,'risks':risks}

            idx=st.session_state.projects.index[st.session_state.projects['Project']==project][0]
            st.session_state.updates.loc[len(st.session_state.updates)] = [
                str(date.today()),project,st.session_state.projects.loc[idx,'Owner'],status,comments
            ]

            st.session_state.projects.loc[idx,'OverallStatus']=status
            st.session_state.projects.loc[idx,'Comments']=comments

            # Saved tables become the new editor base, so clear pending edits to avoid applying them twice
            for k in ('tasks','tests','bugs','risks'):
                st.session_state.pop(f'{k}_{project}',None)
            st.session_state.saved_msg=True
            st.rerun()

        if st.session_state.pop('saved_msg',False):
            st.success('Daily Update Saved')

else:
    banner('Project Status Dashboard','Portfolio overview — status, bugs & risks')

    df=st.session_state.projects.copy()

    if len(df)==0:
        st.info('No projects available')
    else:
        managers=['All']+sorted(df['Manager'].unique().tolist())
        manager=st.selectbox('Filter by Manager',managers)

        if manager!='All':
            df=df[df['Manager']==manager]

        # Open bugs = Open + Reopen across all severities; open risks = risk rows with status Open
        updates=st.session_state.updates
        reports=st.session_state.reports
        df['Open Bugs']=[int(reports[p]['bugs'][['Open','Reopen']].sum().sum()) for p in df['Project']]
        df['Open Risks']=[int((reports[p]['risks']['Status']=='Open').sum()) for p in df['Project']]

        def project_reports(projects):
            for project in projects:
                report=reports[project]
                with st.expander(project):
                    st.markdown('**Task Tracker**')
                    st.dataframe(
                        report['tasks'],width='stretch',hide_index=True,
                        column_config={
                            'Start Date':st.column_config.DateColumn(format='DD-MMM'),
                            'End Date':st.column_config.DateColumn(format='DD-MMM'),
                            '% Complete':st.column_config.NumberColumn(format='%d%%'),
                        },
                    )
                    st.markdown('**Informal Test Execution**')
                    st.dataframe(report['tests'].loc[['Informal']],width='stretch',hide_index=True)
                    st.markdown('**Formal Test Execution**')
                    st.dataframe(report['tests'].loc[['Formal']],width='stretch',hide_index=True)
                    st.markdown('**Bug Bifurcation**')
                    st.dataframe(with_total_row(report['bugs']),width='stretch')
                    st.markdown('**Risk**')
                    st.dataframe(report['risks'],width='stretch',hide_index=True)

        def ratio(n,total):
            # "n / total"; a total of 0 means it hasn't been entered yet
            return f'{int(n)} / {int(total)}' if total else f'{int(n)} / TBD'

        def summary_table(data):
            rows=[]
            for _,r in data.iterrows():
                rep=reports[r['Project']]
                inf,frm=rep['tests'].loc['Informal'],rep['tests'].loc['Formal']
                bugs=rep['bugs']
                bug_total=int(bugs['Total'].sum()) or int(bugs.drop(columns='Total').sum().sum())
                end=pd.to_datetime(rep['tasks']['End Date'],errors='coerce').max()
                rows.append({
                    'Manager':r['Manager'],'Project':r['Project'],'Owner':r['Owner'],'Overall Status':r['OverallStatus'],
                    'Informal TC Executed / Total':ratio(inf['Executed'],inf["Total TC's"]),
                    'Informal Blocked / Total':ratio(inf['Blocked'],inf["Total TC's"]),
                    'Formal TC Executed / Total':ratio(frm['Executed'],frm["Total TC's"]),
                    'Formal Blocked / Total':ratio(frm['Blocked'],frm["Total TC's"]),
                    'Bugs Open / Total':ratio(r['Open Bugs'],bug_total),
                    'End Date':end.strftime('%d-%b') if pd.notna(end) else 'TBD',
                    'Risk':r['Open Risks'],
                })

            # HTML table so headers can wrap and all columns fit on screen
            def cell(col,v):
                if col=='Overall Status':
                    return f'<span class="st-badge" style="background:{STATUS_COLORS.get(v,"#898781")}26">{html.escape(v)}</span>'
                if col=='Risk':
                    color,tip=(BUG_COLOR,f'{v} open risk(s)') if v else ('#0ca30c','No open risk')
                    return f'<span class="dot" style="background:{color}" title="{tip}"></span>'
                if 'Blocked' in col:
                    cls='blocked' if not v.startswith('0 ') else 'ok'
                    return f'<span class="{cls}">{v}</span>'
                return html.escape(str(v))
            cols=list(rows[0])
            head=''.join(f'<th>{c.replace(" / ","<br>/ ") if "TC" in c or "Blocked" in c or "Bugs" in c else c}</th>' for c in cols)
            body=''.join('<tr>'+''.join(f'<td>{cell(c,r[c])}</td>' for c in cols)+'</tr>' for r in rows)
            st.markdown(f'<div class="summary-wrap"><table class="summary"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
                        '<div class="legend"><span class="dot" style="background:#0ca30c"></span> No open risk '
                        f'&nbsp;&nbsp;<span class="dot" style="background:{BUG_COLOR}"></span> Open risk</div>',unsafe_allow_html=True)

        def project_list(data):
            # Simple list used by the Projects / Planning / In Progress / Completed screens
            data=data[['Project','Manager','Owner','OverallStatus']].rename(columns={'OverallStatus':'Status'})
            st.dataframe(data.style.map(tint_status,subset=['Status']),width='stretch',hide_index=True)

        # Each card: (key, label, value, accent, icon)
        cards=[('projects','Projects',len(df),NAVY,'📁')]
        cards+=[(s,s,int((df['OverallStatus']==s).sum()),STATUS_COLORS[s],STATUS_ICONS[s]) for s in PROJECT_STATUSES]
        cards+=[('bugs','Open Bugs',int(df['Open Bugs'].sum()),BUG_COLOR,'🐞'),
                ('risks','Open Risks',int(df['Open Risks'].sum()),RISK_COLOR,'⚠️')]

        view=st.session_state.get('dash_view')

        if view is None:
            home,detail,history=st.tabs(['🏠 Home','📄 Project Detail Report','🕒 Update History'])

            with home:
                st.caption('Click a box to see its details')
                for col,(key,label,value,accent,icon) in zip(st.columns(len(cards)),cards):
                    if kpi_button(col,key,label,value,accent,icon):
                        st.session_state.dash_view=key
                        st.rerun()
                st.write('')
                st.subheader('Project Summary')
                summary_table(df)

            with detail:
                st.caption('Click a project to open its full report')
                project_reports(df['Project'])

            with history:
                hist=updates[updates['Project'].isin(df['Project'])].iloc[::-1]
                if len(hist)==0:
                    st.info('No daily updates saved yet.')
                else:
                    st.caption('Newest update first')
                    st.dataframe(hist,width='stretch',hide_index=True)

        else:
            key,label,value,accent,icon=next(c for c in cards if c[0]==view)
            if st.button('← Back to Dashboard'):
                st.session_state.pop('dash_view')
                st.rerun()
            st.markdown(f'<div class="detail-title" style="--accent:{accent}">{icon} {label} <span>{value}</span></div>',unsafe_allow_html=True)

            if view=='projects':
                with st.container(border=True):
                    st.altair_chart(status_donut(df),width='stretch')
                project_list(df)

            elif view in PROJECT_STATUSES:
                sub=df[df['OverallStatus']==view]
                if len(sub)==0:
                    st.info(f'No projects in {view}.')
                else:
                    project_list(sub)

            elif view=='bugs':
                rows=[]
                for _,r in df.iterrows():
                    b=reports[r['Project']]['bugs']
                    for sev in SEVERITIES:
                        o,ro=int(b.loc[sev,'Open']),int(b.loc[sev,'Reopen'])
                        if o+ro:
                            rows.append({'Project':r['Project'],'Owner':r['Owner'],'Manager':r['Manager'],
                                         'Severity':sev,'Open':o,'Reopen':ro,'Total Open':o+ro})
                if not rows:
                    st.info('No open bugs.')
                else:
                    bugs=pd.DataFrame(rows)
                    by_sev=bugs.groupby('Severity')['Total Open'].sum().reindex(SEVERITIES,fill_value=0)
                    sev_data=pd.DataFrame({'Severity':SEVERITIES,'Open Bugs':by_sev.astype(int).values})
                    with st.container(border=True):
                        st.altair_chart(hbar(sev_data,'Severity','Open Bugs','Open Bugs by Severity',BUG_COLOR),width='stretch')
                    st.markdown('**Open bug list**')
                    st.dataframe(bugs,width='stretch',hide_index=True)

            elif view=='risks':
                rows=[]
                for _,r in df.iterrows():
                    rk=reports[r['Project']]['risks']
                    for _,x in rk[rk['Status']=='Open'].iterrows():
                        # Sr No runs 1..n across the whole list
                        rows.append({'Sr No':len(rows)+1,'Project':r['Project'],'Owner':r['Owner'],'Manager':r['Manager'],
                                     'Risk Detail':x['Risk Detail'],'Status':x['Status']})
                if not rows:
                    st.info('No open risks.')
                else:
                    st.dataframe(pd.DataFrame(rows),width='stretch',hide_index=True,
                                 column_config={'Risk Detail':st.column_config.TextColumn(width='large')})
