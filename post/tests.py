from django.test import TestCase

# Create your tests here.
import axios from 'axios';
import React, {useState, useEffect,useCallback,useRef,useMemo} from 'react'
import {conversationsURL,listtagURL,listThreadlURL,uploadfileURL,createmessageURL,filemessageURL, originurl, creategroupURL} from "../urls"
import { connect } from 'react-redux';
import { headers,expiry, actionchat} from '../actions/auth';
import io from "socket.io-client";
import {debounce} from 'lodash';
import "../css/chat.css"
import Editor from '@draft-js-plugins/editor';
import { EditorState,convertToRaw,Modifier, KeyBindingUtil,getDefaultKeyBinding,convertFromRaw } from 'draft-js';
import createMentionPlugin, {
  defaultSuggestionsFilter,MentionData,MentionPluginTheme,
} from '@draft-js-plugins/mention';
import { number,timeago,listemoji,dataURLtoFile,timevalue,checkDay, listactionchat } from "../constants";
import EmojiPicker from '../hocs/EmojiPicker';
import Entry from "../hocs/Entry";
const style={backgroundSize: 'auto', width: '20px', height: '20px', backgroundRepeat: 'no-repeat', display: 'inline-block'}
const Chatbody=(props)=>{
    const {datalistmember,thread,datamessages,user,height,listuserdata,setlisttags,listtags}=props
    const [state, setState] = useState({loading_more:false,list_file_chat:[],loading:true});
    const [shop,setShop]=useState({list_orders:[],list_items:[],count_product:0,count_order:0,choice:null})
    const [list_messages,setListmessages]=useState([]);
    const [message,setMessage]=useState('')
    const [listimage,setListimage]=useState([]);
    const [listfile,setListfile]=useState([]);
    const [showemoji,setShowemoji]=useState(false)
    const [group,setGroup]=useState(false)
    const [typing,setTyping]=useState({typing:false,receiver:[]})
    const [open, setOpen] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const [show, setShow] = useState(false);
    const [listmember,setListmember]=useState([])
    const [receiver,setReceiver]=useState([])
    const [listuser,setListuser]=useState([])
    const socket=useRef()   
    const scrollRef=useRef(null);
    const [length,setLength]=useState(50)
    const ref=useRef()
    const [editorState, setEditorState] = useState(() =>
        EditorState.createEmpty()
    );
    useEffect(()=>{
        if(listuserdata){
        setListuser(listuserdata)
        }
    },[listuserdata])
    const { MentionSuggestions, plugins } = useMemo(() => {
    const mentionPlugin = createMentionPlugin({
      entityMutability: 'IMMUTABLE',
      supportWhitespace: true,
    });
    
    // eslint-disable-next-line no-shadow
    const { MentionSuggestions } = mentionPlugin;
    // eslint-disable-next-line no-shadow
    const plugins = [mentionPlugin];
        return { plugins, MentionSuggestions };
    }, []);
    
    
    const onChange = (editorState) => {
        setEditorState(editorState);
        sentyping(editorState)
    }

    const onOpenChange = () => {
        setOpen(!open);
    }

    const rawContentState = convertToRaw(editorState.getCurrentContent());
    const onSearchChange =({ value }) => {
        if(group){
        fetchkeyword(value) 
        setSuggestions(defaultSuggestionsFilter(value, suggestions));
        }
    }

   const creategroup=()=>{
       let form=new FormData()
       axios.post(creategroupURL,form,headers)
   }
    const fetchkeyword=useCallback(debounce((value)=>{
        (async ()=>{
            try{
                const res = await axios.get(`${listtagURL}?keyword=${value}`,headers)
                
                setSuggestions(res.data)
            }
            catch{
                console.log('error')
            }
        })()
    },1000),[])

    
    useEffect(() => {
        socket.current=io.connect('https://web-production-e133.up.railway.app')
        socket.current.on('message',data=>{
            console.log(data)
            if(data.typing || data.typing==""){
                if(data.typing==""){
                    setTyping({typing:false})
                }
                else{
                setTyping({typing:true})
                setReceiver(data.receiver)
                }
            }
            else{
                const message_text={user_id:data.send_by,message:data.message,list_file:[],date_created:new Date().toString()}
                const message_file=data.list_file.filter(item=>item.filetype!='image').map(item=>{
                    return({user_id:data.send_by,message:null,list_file:[item],date_created:new Date().toString()})
                })
                
                const message_image={user_id:data.send_by,message:null,list_file:data.list_file.filter(item=>item.filetype=='image'),date_created:new Date().toString()}
                const list=data.message && data.list_file.length>0?[...list_messages,message_text,message_image,...message_file]:data.message?[...list_messages,message_text]:data.list_file.length>0?[...list_messages,message_image,...message_file]:list_messages
                setTyping({typing:false,send_to:data.send_to})
                
                if(thread){
                    setListmessages(list)
                }
            }
            if(scrollRef.current){
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight
            }
        })
        
        return () => {
            socket.current.disconnect();
          };
    },[list_messages,scrollRef,thread]);
    
   
   
    //list thread
    useEffect(() =>  {
        setListmember(datalistmember)
        setListmessages(datamessages)
    }, [datalistmember,datamessages]);


    const sentyping= useCallback(debounce((value)=>{
        const rawContentState = convertToRaw(value.getCurrentContent());
        let data={
        typing:rawContentState.blocks[0].text,
        send_by: user.id,
        receiver:listmember.filter(member=>user.id!=member.id),
        count_uploadfile: state.list_file_chat.length
        }
        
        socket.current.emit('sendData',data)
    },1000),[user,listmember,editorState])
    const listfileupload=[...listimage,...listfile]
    const senmessage=(e)=>{
        let form=new FormData()
        form.append('action','create-message')
        form.append('send_by',user.id)
        if(rawContentState.blocks[0].text.trim()!=''){
            form.append('message',rawContentState.blocks[0].text)
        }
        listimage.map(file=>{
            form.append('image',file.file)
        })
        axios.post(`${conversationsURL}/${thread}`,form,headers)
        .then(res=>{
            setListimage([])
        })
        listfile.map((file,i)=>{
            let formfile=new FormData()
            formfile.append('action','create-message')
            formfile.append('send_by',user.id)
            if(file.filetype=='video'){
                formfile.append('video',file.file)
                formfile.append('video_preview',file.file_preview)
                formfile.append('duration',file.duration)
            }
            else{
                formfile.append('file',file.file)
                formfile.append('name',file.file_name)
            }
            axios.post(`${conversationsURL}/${thread}`,formfile,headers)
            .then(res=>{
                const files=listfile.splice(i,1)
                setListfile(files)
            })
        })  
        setShowemoji(false)
        setEditorState(EditorState.createEmpty())
    }
    
    const setaddkey=(e,text)=>{  
        setEditorState(insertText(text, editorState));
    }
    const insertText = (text, editorValue) => {
        const currentContent = editorValue.getCurrentContent();
        const currentSelection = editorValue.getSelection();
        const newContent = Modifier.replaceText(
        currentContent,
        currentSelection,
        text
    );
        const newEditorState = EditorState.push(
        editorValue,
        newContent,
        "insert-characters"
        );
        return EditorState.forceSelection(
        newEditorState,
        newContent.getSelectionAfter()
        );
    };
    
    //add message
    const addmessage=(e)=>{
        e.stopPropagation()
        if(state.loading && e.target.scrollTop==0 && list_messages.length<message.thread_choice.count_message){
            setState({...state,loading:false})
            let url= new URL(listThreadlURL)
            let search_params=url.searchParams
            search_params.set('thread_id',message.thread_choice.id)
            search_params.set('offset',list_messages.length)
            url.search = search_params.toString();
            let new_url = url.toString();
            axios.get(new_url,headers)
            .then(res=>{
                setState({...state,loading:true})
                const list_message=[...res.data.messages,...list_messages]
                e.target.scrollTop = 60
                setListmessages(list_message)
            })
        }
        else{
            setState({...state,loading:true}) 
        }
    }

    //input click
    const onBtnClick=(e)=>{
        console.log(e.currentTarget)
        e.currentTarget.querySelector('input').click()
    }

    const listdate=()=>{
        let list_days_unique=[]
        let list_days=[]
        const list_day=list_messages.map(message=>{
            return(("0" + new Date(message.date_created).getDate()).slice(-2) + "-" + ("0"+(new Date(message.date_created).getMonth()+1)).slice(-2) + "-" +
            new Date(message.date_created).getFullYear())
        })
        for(let j=0;j<list_day.length;j++){
            if(list_days[list_day[j]]) continue;
            list_days[list_day[j]] = true;
            list_days_unique.push(j)
        }
        return list_days_unique
    }
   
    let list_file=[]
    let list_image=[]
    const previewFile=(e)=>{
        [].forEach.call(e.target.files, function(file) {
            if ((/image\/.*/.test(file.type))){
                list_image.push({file:file,file_preview:undefined,duration:0,filetype:'image',
                file_name:file.name,media_preview:(window.URL || window.webkitURL).createObjectURL(file)})
                const list_file_chat=[...listimage,...list_image]
                setListimage(list_file_chat)
            }
            else if(file.type.match('video.*')){ 
                var url = (window.URL || window.webkitURL).createObjectURL(file);
                var video = document.createElement('video');
                var timeupdate = function() {
                if (snapImage()) {
                    video.removeEventListener('timeupdate', timeupdate);
                    video.pause();
                  }
                };
                video.addEventListener('loadeddata', e =>{
                        
                if (snapImage()) {
                    video.removeEventListener('timeupdate', timeupdate);
                  }
                });
                let snapImage = function() {
                let canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                let image = canvas.toDataURL("image/png");
                let file_preview = dataURLtoFile(image,'dbc9a-rg53.png');
                let success = image.length > 100000;
                if (success) {
                    list_file.push({file_name:file.name,filetype:'video',file:file,file_preview:file_preview,duration:video.duration,media_preview:(window.URL || window.webkitURL).createObjectURL(file_preview)})    
                    const list_file_chat=[...listfile,...list_file]
                    setListfile(list_file_chat)
                }
                return success;
                };
                video.addEventListener('timeupdate', timeupdate);
                video.preload = 'metadata';
                video.src = url;
                // Load video in Safari / IE11
                video.muted = true;
                video.playsInline = true;
                video.play();
                }
                else{
                    list_file.push({file_name:file.name,filetype:'pdf',file:file})   
                    const list_file_chat=[...listfile,...list_file]
                    setListfile(list_file_chat)
                }
            })
    }

    const deletefile=(file,i)=>{
        let form=new FormData()
        state.list_file_chat.splice(i,1)
        setState({...state,list_file_chat:state.list_file_chat})
    }                

    const sendto=(e)=>{

    }
    const myKeyBindingFn=(e)=>{
        const { hasCommandModifier } = KeyBindingUtil;
        if (e.keyCode === 13 && !hasCommandModifier(e)) {
            senmessage(e)
        }
        return getDefaultKeyBinding(e);
    }

    
    ///set tychat
    const settypechat=(item)=>{
        setState({...state,type_chat:item.value})
        let url= new URL(listThreadlURL)
        let search_params=url.searchParams
        axios.get(`${listThreadlURL}?type_chat=${item.value.toString()}`,headers)
        .then(res=>{
            setState({...state,show_type_chat:false})
            if(!res.data.some(item=>item.id==message.thread_choice.id)){
                setMessage('')
                setListmessages([])
            }
        })
    }

    const forward=(e,item)=>{
        const datachat={...item,action:'forward',show:true}
        actionchat(datachat)
    }

    
    return(
        <div className="chat-body">
            <div className="chat-window-detail">
                <div className="chat-message-detail">
                {listuser.length>0?
                <div>
                    {listuser.map(mention=>
                        <div onClick={()=>{
                            setlisttags([...listtags,mention])
                            setListuser([])
                            setState({...state,text:''})
                        }} key={mention.id} data-e2e="comment-at-list" className="tiktok-d4c6zy-DivItemBackground ewopnkv6">
                            <div className="tiktok-1rn2hi8-DivItemContainer ewopnkv5 item-space">
                                <span shape="circle" className="tiktok-tuohvl-SpanAvatarContainer e1e9er4e0" style={{flex: '0 0 40px', width: '40px', height: '40px'}}>
                                    <img loading="lazy" src={mention.avatar} className="tiktok-1zpj2q-ImgAvatar e1e9er4e1"/>
                                </span>
                                <div className="tiktok-4f7266-DivInfoContainer ewopnkv7">
                                    <p className="tiktok-15s5y80-PMentionInfoLine ewopnkv8">
                                        <span data-e2e="comment-at-nickname" className="tiktok-evv4sm-SpanInfoNickname ewopnkv9">{mention.name}</span>
                                            <span className="tiktok-14bueqa-SpanInfoVerify ewopnkv12">
                                            <svg className="tiktok-shsbhf-StyledVerifyBadge e1aglo370" width="1em" height="1em" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="24" cy="24" r="24" fill="#20D5EC"></circle><path fillRule="evenodd" clipRule="evenodd" d="M37.1213 15.8787C38.2929 17.0503 38.2929 18.9497 37.1213 20.1213L23.6213 33.6213C22.4497 34.7929 20.5503 34.7929 19.3787 33.6213L10.8787 25.1213C9.70711 23.9497 9.70711 22.0503 10.8787 20.8787C12.0503 19.7071 13.9497 19.7071 15.1213 20.8787L21.5 27.2574L32.8787 15.8787C34.0503 14.7071 35.9497 14.7071 37.1213 15.8787Z" fill="white"></path></svg>
                                        </span>
                                    </p>
                                    <p className="tiktok-15s5y80-PMentionInfoLine ewopnkv8">
                                        <span data-e2e="comment-at-uniqueid" className="tiktok-ny41l3-SpanInfoUniqueId ewopnkv10">Bạn bè</span>
                                    </p>
                                </div>
                                
                            </div>
                            
                        </div>
                    )}
                </div>:
                <div className="chat-message-detail-wrap" id="messagesContainer">      
                    {listfileupload.length>0?
                    <div className="chat-mediapreview-wrap">
                        <section className="chat-mediapreview-section">
                            <div className="chat-mediapreview-section-content">
                                <div className="chat-mediapreview-section-files">   
                                    {listfileupload.map((file,i)=>{
                                        if(file.filetype=="image" || file.filetype=="video"){
                                            return(
                                                <div className="vbUibIOQCdVGpvTHR9QZ5" key={i}>
                                                    <img className="_3KQNXANNUSJKR1Z2adRPjF" src={file.media_preview} />
                                                    {file.filetype=="video"?
                                                    <i className="_3kEAcT1Mk5 _3Fs5Tyt_FBVBTwz60zkqsd">
                                                        <svg viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="17" cy="17" r="16.3333" fill="black" fill-opacity="0.5" stroke="white" strokeWidth="0.666667"></circle><path fillRule="evenodd" clip-rule="evenodd" d="M23.0444 16.2005C23.5778 16.6005 23.5778 17.4005 23.0444 17.8005L15.0444 23.8005C14.3852 24.2949 13.4444 23.8245 13.4444 23.0005L13.4444 11.0005C13.4444 10.1764 14.3852 9.70606 15.0444 10.2005L23.0444 16.2005Z" fill="white"></path></svg>
                                                    </i>:''}
                                                    <i onClick={()=>deletefile(file,i)} className="icon-chat-message-delete">
                                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="8" fill="#8EA4D1"></circle><path fillRule="evenodd" clip-rule="evenodd" d="M8 9.26316L10.7368 12L12 10.7368L9.26316 8L12 5.26316L10.7368 4L8 6.73684L5.26316 4L4 5.26316L6.73684 8L4 10.7368L5.26316 12L8 9.26316Z" fill="white"></path></svg>
                                                    </i>
                                                </div>
                                            )
                                        }
                                        else{
                                            return(
                                                <div className="item-center chat-item vbUibIOQCdVGpvTHR9QZ5 taijpn5t" key={i}>
                                                    <i onClick={()=>deletefile(file,i)} className="icon-chat-message-delete">
                                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="8" fill="#8EA4D1"></circle><path fillRule="evenodd" clip-rule="evenodd" d="M8 9.26316L10.7368 12L12 10.7368L9.26316 8L12 5.26316L10.7368 4L8 6.73684L5.26316 4L4 5.26316L6.73684 8L4 10.7368L5.26316 12L8 9.26316Z" fill="white"></path></svg>
                                                    </i>
                                                    <div className="s45kfl79 emlxlaya item-center">
                                                        <i className="chat-icon">
                                                            <svg xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" width="45.057px" height="45.057px" viewBox="0 0 45.057 45.057" style={{enableBackground:'new 0 0 45.057 45.057'}} xmlSpace="preserve">
                                                                <g id="_x35_1_80_">
                                                                    <path d="M13.323,13.381c6.418,0,12.834,0,19.252,0c1.613,0,1.613-2.5,0-2.5c-6.418,0-12.834,0-19.252,0     C11.711,10.881,11.711,13.381,13.323,13.381z"/>
                                                                    <path d="M32.577,16.798c-6.418,0-12.835,0-19.253,0c-1.612,0-1.612,2.5,0,2.5c6.418,0,12.835,0,19.253,0     C34.188,19.298,34.188,16.798,32.577,16.798z"/>
                                                                    <path d="M32.577,22.281c-6.418,0-12.835,0-19.253,0c-1.612,0-1.612,2.5,0,2.5c6.418,0,12.835,0,19.253,0     C34.188,24.781,34.188,22.281,32.577,22.281z"/>
                                                                    <path d="M32.577,28.197c-6.418,0-12.835,0-19.253,0c-1.612,0-1.612,2.5,0,2.5c6.418,0,12.835,0,19.253,0     C34.188,30.697,34.188,28.197,32.577,28.197z"/>
                                                                    <path d="M32.204,33.781c-6.418,0-12.834,0-19.252,0c-1.612,0-1.612,2.5,0,2.5c6.418,0,12.834,0,19.252,0     C33.817,36.281,33.817,33.781,32.204,33.781z"/>
                                                                    <path d="M33.431,0H5.179v45.057h34.699V6.251L33.431,0z M36.878,42.056H8.179V3h23.707v4.76h4.992V42.056z"/>
                                                                </g>
                                                            </svg>
                                                        </i>
                                                    </div>
                                                    <div className="buofh1pr oo9gr5id item-center">
                                                        <span className="mau55g9w c8b282yb d3f4x2em iv3no6db">
                                                            <span className="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7" style={{webkitBoxOrient: 'vertical', webkitLineClamp: 2, display: '-webkit-box'}}>{file.file_name}</span>
                                                        </span>
                                                    </div>
                                                </div>
                                            )
                                        }
                                    })}
                                    <div onClick={(e)=>onBtnClick(e)} className="">
                                        <div>
                                            <input onChange={(e)=>previewFile(e)} accept="video/*,.flv,.3gp,.rm,.rmvb,.asf,.mp4,.webm,image/png,image/jpeg,image/jpg" multiple="" type="file" style={{display: 'none'}}/>
                                            <div className="add-file">
                                                <i className="icon-add-file _3kEAcT1Mk5">
                                                    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="0.5" y="14.5" width="31" height="3" fill="#8EA4D1" stroke="#8EA4D1"></rect><rect x="17.5" y="0.5" width="31" height="3" transform="rotate(90 17.5 0.5)" fill="#8EA4D1" stroke="#8EA4D1"></rect></svg>
                                                </i>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div onClick={e=>setState({...state,list_file_chat:[]})} className="chat-message-action">
                                <i className="icon-message">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" className="chat-icon"><path d="M-1595 1c-282.8 0-512 229.2-512 512s229.2 512 512 512 512-229.2 512-512S-1312.2 1-1595 1zm313.3 380.4l-362 362c-16.7 16.7-43.7 16.7-60.3 0l-201.1-201.1c-16.7-16.7-16.7-43.7 0-60.3 16.7-16.7 43.7-16.7 60.3 0l171 171 331.8-331.9c16.7-16.7 43.7-16.7 60.3 0 16.7 16.6 16.7 43.7 0 60.3zM-117.3 42.7h-853.3c-23.6 0-42.7 19.1-42.7 42.7v853.3c0 23.6 19.1 42.7 42.7 42.7h853.3c23.6 0 42.7-19.1 42.7-42.7V85.3c-.1-23.5-19.2-42.6-42.7-42.6zm-115.4 340.7l-362 362c-16.7 16.7-43.7 16.7-60.3 0l-201.1-201.1c-16.7-16.7-16.7-43.7 0-60.3 16.7-16.7 43.7-16.7 60.3 0l171 171L-293 323.1c16.7-16.7 43.7-16.7 60.3 0 16.7 16.6 16.7 43.7 0 60.3zM601.9 512.1l402.3-401.5c25.1-25 25.1-65.7.1-90.8-25-25.1-65.7-25.1-90.8-.1L511.1 421.4 108.6 19.7c-25.1-25-65.7-25-90.8.1-25 25.1-25 65.7.1 90.8l402.3 401.5L17.9 913.6c-25.1 25-25.1 65.7-.1 90.8s65.7 25.1 90.8.1l402.5-401.7 402.5 401.7c25.1 25 65.7 25 90.8-.1s25-65.7-.1-90.8L601.9 512.1z"></path></svg>
                                </i>
                            </div>
                        </section>
                    </div>:''}
                    <div ref={scrollRef} onScroll={(e)=>addmessage(e)} className="chat-message-container" style={{overflowX: 'hidden',boxSizing: 'border-box',direction: 'ltr',height: `${height-parseInt(rawContentState.blocks[0].text.length/length)*20}px`,position: 'relative',padding: '0 7.5px',willChange: 'transform',overflowY: 'auto'}}> 
                        {state.loading?'':<div className="item-centers">
                            <div className="loader"></div>
                        </div>}
                        
                    </div>
                </div>
                }
                {listuser.length>0?'':
                <div className="chat-input">
                    <div className="chat-input-field-index flex">
                        <div className="chat-index__toolbar">
                            <div className="chat-inputfield-toolbar">
                                <div className="flex flex-center">
                                    
                                    <div className="" onClick={()=>setShowemoji(!showemoji)}>
                                        <div className="chat-inputfield-toolbar-icon">
                                                
                                            <svg viewBox="0 0 24 24" height="20px" width="20px" class="a8c37x1j ms05siws hr662l2t b7h9ocf4 crt8y2ji tftn3vyl"><g fill-rule="evenodd"><polygon fill="none" points="-6,30 30,30 30,-6 -6,-6 "></polygon><path d="m18,11l-5,0l0,-5c0,-0.552 -0.448,-1 -1,-1c-0.5525,0 -1,0.448 -1,1l0,5l-5,0c-0.5525,0 -1,0.448 -1,1c0,0.552 0.4475,1 1,1l5,0l0,5c0,0.552 0.4475,1 1,1c0.552,0 1,-0.448 1,-1l0,-5l5,0c0.552,0 1,-0.448 1,-1c0,-0.552 -0.448,-1 -1,-1m-6,13c-6.6275,0 -12,-5.3725 -12,-12c0,-6.6275 5.3725,-12 12,-12c6.627,0 12,5.3725 12,12c0,6.6275 -5.373,12 -12,12"></path></g></svg>
                                                
                                        </div>
                                    </div>
                                    
                                    {rawContentState.blocks[0].text==''?<>
                                    
                                        <div className="" onClick={(e)=>onBtnClick(e)}>
                                            <input onChange={(e)=>previewFile(e)}  multiple={true} type="file" style={{display: 'none'}}/>
                                            <div className="chat-inputfield-toolbar-icon">
                                                
                                                <svg viewBox="0 -1 17 17" height="20px" width="20px" class="a8c37x1j ms05siws hr662l2t b7h9ocf4"><g fill="none" fill-rule="evenodd"><path d="M2.882 13.13C3.476 4.743 3.773.48 3.773.348L2.195.516c-.7.1-1.478.647-1.478 1.647l1.092 11.419c0 .5.2.9.4 1.3.4.2.7.4.9.4h.4c-.6-.6-.727-.951-.627-2.151z" class="crt8y2ji"></path><circle cx="8.5" cy="4.5" r="1.5" class="crt8y2ji"></circle><path d="M14 6.2c-.2-.2-.6-.3-.8-.1l-2.8 2.4c-.2.1-.2.4 0 .6l.6.7c.2.2.2.6-.1.8-.1.1-.2.1-.4.1s-.3-.1-.4-.2L8.3 8.3c-.2-.2-.6-.3-.8-.1l-2.6 2-.4 3.1c0 .5.2 1.6.7 1.7l8.8.6c.2 0 .5 0 .7-.2.2-.2.5-.7.6-.9l.6-5.9L14 6.2z" class="crt8y2ji"></path><path d="M13.9 15.5l-8.2-.7c-.7-.1-1.3-.8-1.3-1.6l1-11.4C5.5 1 6.2.5 7 .5l8.2.7c.8.1 1.3.8 1.3 1.6l-1 11.4c-.1.8-.8 1.4-1.6 1.3z" stroke-linecap="round" stroke-linejoin="round" class="s9lmpwuu"></path></g></svg>
                                                
                                            </div>
                                        </div>
                                    
                                    
                                        <div>
                                            
                                            <div className="chat-inputfield-toolbar-icon">
                                                
                                            <svg x="0px" y="0px" viewBox="0 0 17 16" height="20px" width="20px" class="a8c37x1j ms05siws hr662l2t b7h9ocf4 crt8y2ji"><g fill-rule="evenodd"><circle fill="none" cx="5.5" cy="5.5" r="1"></circle><circle fill="none" cx="11.5" cy="4.5" r="1"></circle><path d="M5.3 9c-.2.1-.4.4-.3.7.4 1.1 1.2 1.9 2.3 2.3h.2c.2 0 .4-.1.5-.3.1-.3 0-.5-.3-.6-.8-.4-1.4-1-1.7-1.8-.1-.2-.4-.4-.7-.3z" fill="none"></path><path d="M10.4 13.1c0 .9-.4 1.6-.9 2.2 4.1-1.1 6.8-5.1 6.5-9.3-.4.6-1 1.1-1.8 1.5-2 1-3.7 3.6-3.8 5.6z"></path><path d="M2.5 13.4c.1.8.6 1.6 1.3 2 .5.4 1.2.6 1.8.6h.6l.4-.1c1.6-.4 2.6-1.5 2.7-2.9.1-2.4 2.1-5.4 4.5-6.6 1.3-.7 1.9-1.6 1.9-2.8l-.2-.9c-.1-.8-.6-1.6-1.3-2-.7-.5-1.5-.7-2.4-.5L3.6 1.5C1.9 1.8.7 3.4 1 5.2l1.5 8.2zm9-8.9c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1zm-3.57 6.662c.3.1.4.4.3.6-.1.3-.3.4-.5.4h-.2c-1-.4-1.9-1.3-2.3-2.3-.1-.3.1-.6.3-.7.3-.1.5 0 .6.3.4.8 1 1.4 1.8 1.7zM5.5 5.5c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1z" fill-rule="nonzero"></path></g></svg>
                                                
                                            </div>
                                        </div>
                                
                                        <div className="">
                                            <div className="chat-inputfield-toolbar-icon">
                                                
                                                <svg x="0px" y="0px" viewBox="0 0 16 16" height="20px" width="20px" class="a8c37x1j ms05siws hr662l2t b7h9ocf4 crt8y2ji"><path d="M.783 12.705c.4.8 1.017 1.206 1.817 1.606 0 0 1.3.594 2.5.694 1 .1 1.9.1 2.9.1s1.9 0 2.9-.1 1.679-.294 2.479-.694c.8-.4 1.157-.906 1.557-1.706.018 0 .4-1.405.5-2.505.1-1.2.1-3 0-4.3-.1-1.1-.073-1.976-.473-2.676-.4-.8-.863-1.408-1.763-1.808-.6-.3-1.2-.3-2.4-.4-1.8-.1-3.8-.1-5.7 0-1 .1-1.7.1-2.5.5s-1.417 1.1-1.817 1.9c0 0-.4 1.484-.5 2.584-.1 1.2-.1 3 0 4.3.1 1 .2 1.705.5 2.505zm10.498-8.274h2.3c.4 0 .769.196.769.696 0 .5-.247.68-.747.68l-1.793.02.022 1.412 1.252-.02c.4 0 .835.204.835.704s-.442.696-.842.696H11.82l-.045 2.139c0 .4-.194.8-.694.8-.5 0-.7-.3-.7-.8l-.031-5.631c0-.4.43-.696.93-.696zm-3.285.771c0-.5.3-.8.8-.8s.8.3.8.8l-.037 5.579c0 .4-.3.8-.8.8s-.8-.4-.8-.8l.037-5.579zm-3.192-.825c.7 0 1.307.183 1.807.683.3.3.4.7.1 1-.2.4-.7.4-1 .1-.2-.1-.5-.3-.9-.3-1 0-2.011.84-2.011 2.14 0 1.3.795 2.227 1.695 2.227.4 0 .805.073 1.105-.127V8.6c0-.4.3-.8.8-.8s.8.3.8.8v1.8c0 .2.037.071-.063.271-.7.7-1.57.991-2.47.991C2.868 11.662 1.3 10.2 1.3 8s1.704-3.623 3.504-3.623z" fill-rule="nonzero"></path></svg>
                                                
                                            </div>
                                            
                                        </div>
                                    
                                    </>:''}
                                </div>
                            </div>
                        </div>
                        <div style={{height:`${30+parseInt(rawContentState.blocks[0].text.length/length)*20}px`}} className="chat-inputfield-chateditor-index__root">
                        <div className="input-chat"> 
                            <div className="tiktok-1vplah5-DivLayoutContainer e1npxakq1">  
                            <div className="tiktok-1vplah5-DivLayoutContainer e1npxakq1">   
                                <div onClick={()=>ref.current.focus()} data-e2e="comment-input" className="tiktok-1vwgyq9-DivInputAreaContainer e1npxakq2">    
                                    <div  data-e2e="comment-text" className="oo9gr5id tiktok-qpucp9-DivInputEditorContainer e1npxakq3">
                                        <Editor
                                            editorKey={'editor'}
                                            editorState={editorState}
                                            onChange={onChange}
                                            plugins={plugins}
                                            ref={ref}
                                            keyBindingFn={myKeyBindingFn}
                                            placeholder="Aa"
                                        />
                                    </div>
                                    {group?
                                    <MentionSuggestions
                                        open={open}
                                        onOpenChange={onOpenChange}
                                        suggestions={suggestions}
                                        onSearchChange={onSearchChange}
                                        onAddMention={(obj) => {
                                            setListuser([...listuser,obj.username])
                                            
                                        }}
                                        entryComponent={Entry}
                                        popoverContainer={({ children }) => 
                                        <div className="tiktok-2qnxeb-DivMentionSuggestionContainer e1npxakq7">
                                            <div className="tiktok-16el7uh-DivContainer ewopnkv0">
                                                <div className="tiktok-16el7uh-DivContainer ewopnkv0">
                                                    {children}
                                                </div>
                                            </div>
                                        </div>}
                                    />
                                    :''}
                                </div>
                            </div>
                            </div>
                            </div>
                            <EmojiPicker
                            showemoji={showemoji}
                            setshowemoji={(data)=>setShowemoji(data)}
                            setaddkey={(e,text)=>setaddkey(e,text)}
                            />
                        </div>
                        <div onClick={(e)=>senmessage(e)} className="chat-send-btn">
                            <div className="chat-send-tooltip">
                                <i className="_3kEAcT1Mk5 chat-index__button">
                                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="chat-icon"><path d="M4 14.497v3.724L18.409 12 4 5.779v3.718l10 2.5-10 2.5zM2.698 3.038l18.63 8.044a1 1 0 010 1.836l-18.63 8.044a.5.5 0 01-.698-.46V3.498a.5.5 0 01.698-.459z"></path></svg>
                                </i>
                            </div>
                        </div>
                    </div>
                </div>}
            </div>
        </div>
        </div>
    )
}
export default Chatbody