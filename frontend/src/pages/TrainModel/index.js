import * as moment from 'moment';
import React, { Component } from 'react';
import { ConfigContainer } from '../../styles/ConfigContainer';
import { default as CustomButton } from '../../styles/Button';
import {
  Header, Table, HeaderColumn, ItemColumn,
  FirstHeaderColumn, FirstItemColumn,
  StatusMsgContainer, LoadingContainer
} from '../../styles/global';
import { connect } from 'react-redux';
import PerfectScrollbar from 'react-perfect-scrollbar';
import { Creators as TrainModelActions } from '../../store/ducks/train_model';
import { Creators as ModelCopyActions } from '../../store/ducks/model_copy';
import { Creators as DialogActions } from '../../store/ducks/dialog';
import { Creators as DownloadActions } from '../../store/ducks/download';
import { actions as toastrActions } from 'react-redux-toastr';
import { Menu, MenuItem } from '@material-ui/core';
import MoreIcon from 'react-feather/dist/icons/more-horizontal';
import CopyIcon from 'react-feather/dist/icons/copy';
import KeyIcon from 'react-feather/dist/icons/key';
import DownloadIcon from 'react-feather/dist/icons/download';
import CodeIcon from 'react-feather/dist/icons/terminal';
import TrashIcon from 'react-feather/dist/icons/trash';
import { primaryColor } from '../../styles/global';
import { PRE_PROCESSING_RAW, TRAIN_PIPELINES } from '../../constants';
import AlertDialog from '../../components/AlertDialog';
import { ProgressSpinner } from 'primereact/progressspinner';
import api from '../../services/api';
import './styles.css';

class TrainModel extends Component {

  constructor(props) {
    super(props);

    this.state = {
      itemSelected: null,
      anchorEl: null,
      models: {},
      loading: true,
    };
  }
  
  getModels = () => {
    const period = document.getElementById('period').value;
    const feature = document.getElementById('feature').value;

    api
      .post(`trained-model?period=${period}&feature=${feature}`)
      .then(response => {
        this.setState({ models: response.data});
      })
      .finally( this.setState( { loading: false }));
  };

  getModelsImg = (initials) => {
    const period = document.getElementById('period').value;
    const feature = document.getElementById('feature').value;
    const index = this.state.itemSelected.itemIdx;
    api
      .post(`trained-model-image?period=${period}&feature=${feature}&time=${index}&initials=${initials}`, {responseType: 'blob'})
      .then(response => {
        var a = document.createElement("a"); //Create <a>
        a.href = "data:image/png;base64," + response.data; //Image Base64 Goes here
        a.download = "Image.png"; //File name Here
        a.click(); //Downloaded file
      })
      .finally( this.setState( { loading: false }));
  };

  getModelsPipeline = (initials) => {
    const period = document.getElementById('period').value;
    const feature = document.getElementById('feature').value;
    const index = this.state.itemSelected.itemIdx;
    api
      .post(`model-pipeline?period=${period}&feature=${feature}&time=${index}&initials=${initials}`)
      .then(response => {
        this.createAndDownloadFile(initials + '.pkl', response.data)
      })
      .finally( this.setState( { loading: false }));
  };




  componentDidMount() {
    this.getModels();
  }

  renderItem = (item, idx, typeOfModel) => (
    <tr key={idx}>      
      <FirstItemColumn>{typeOfModel}</FirstItemColumn>
      <ItemColumn>{item.Name}</ItemColumn>
      <ItemColumn>{item.Accuracy}</ItemColumn>
      <ItemColumn>{item.F1}</ItemColumn>
      <ItemColumn>{item.Prec}</ItemColumn>
      <ItemColumn isClickable onClick={this.handleClickMenu.bind(this, item)}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><MoreIcon size={16} /></div>
      </ItemColumn>
    </tr>
  )

  handleMenuItemClose = () => this.setState({ anchorEl: null });

  handleClickMenu = (item, event) => {
    this.setState({ anchorEl: event.currentTarget, itemSelected: item });
  };

  renderMenuActions = () => {
    let actions = [
      {
        action: 'download_pipeline',
        label: 'Baixar código do modelo',
        icon: <CodeIcon size={16} color={primaryColor} />
      },
      {
        action: 'visualize_matrix',
        label: 'Matriz de confusão',
        icon: <DownloadIcon size={16} color={primaryColor} />
      },
      {
        action: 'download_model_pipeline',
        label: 'Pipeline do Modelo',
        icon: <CopyIcon size={16} color={primaryColor} />
      }      
    ];

    const { anchorEl } = this.state;

    return (
      <Menu
        style={{ list: { paddingTop: 0, paddingBottom: 0 } }}
        id="lock-menu"
        anchorEl={anchorEl}
        keepMounted
        open={Boolean(anchorEl)}
        onClose={this.handleMenuItemClose}
      >
        {actions.map((option, index) => (
          <MenuItem
            style={{ color: primaryColor, fontSize: '14px' }}
            key={index}
            selected={false}
            onClick={this.handleMenuItemClick.bind(this, option)}
          >
            {option.icon}&nbsp;&nbsp;{option.label}
          </MenuItem>
        ))}
      </Menu>
    )
  }

  renderSuccessMsg = ({ title, message }) => {
    this.props.add({
      type: 'success',
      title: title || 'Sucesso',
      message
    });
  }

  handleMenuItemClick = (option, event ) => {
    if (option.action === 'download_pipeline') {
      this.createAndDownloadFile(`${this.state.itemSelected.Name}.txt`, `${this.state.itemSelected.Model}`);
    }

    if (option.action === 'visualize_matrix') {
      this.getModelsImg(this.state.itemSelected.initials);
    }
    
    if (option.action === 'download_model_pipeline') {
      this.getModelsPipeline(this.state.itemSelected.initials);
    }

    this.handleMenuItemClose();
  };

  createAndDownloadFile(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
  
    element.style.display = 'none';
    document.body.appendChild(element);
  
    element.click();
  
    document.body.removeChild(element);
  }
  
  render() {
    const typesOfModels = ['Total (T+1)', 'Total (T+2)', 'Total (T+3)']
    const data = this.state.models || [];
    const loading = this.state.loading;

    return (
      <PerfectScrollbar style={{ width: '100%', overflowX: 'auto' }}>
        <ConfigContainer size='big' style={{ color: '#000' }}>

          <Header >
            <h1>Modelos Salvos</h1>
            <div className='filtros'>
            <div className='dropdown-style'>
              <label className='dropdown-label'>Modelo de previsão para:</label>
              <select name="period" id="period" onChange={this.changePeriod} className='select-style'>
                <option value="Dia">Dia</option>
                <option value="Hora">Hora</option>
              </select>
            </div>
            <div className='dropdown-style'>
              <label className='dropdown-label'>Modelo de previsão com:</label>
              <select name="feature" id="feature" onChange={this.changeFeature} className='select-style'>
                <option value="ALL">ALL</option>
                <option value="FS">Seleção de Features</option>
              </select>
            </div>
            <CustomButton className='button-style'              
              filled={false} onClick={this.getModels}>Confirmar</CustomButton>
            </div>

          </Header>


          {Object.keys(data).length === 0 && !loading ?
            <StatusMsgContainer> Sem modelos salvos para serem exibidos. </StatusMsgContainer>
            : null}

          {loading ?
            <LoadingContainer>
              <ProgressSpinner style={{ width: '50px', height: '50px' }} strokeWidth="4" fill="#EEEEEE" animationDuration=".5s" />
            </LoadingContainer>
            : null}

          {Object.keys(data).length !== 0 && !loading ?
            <Table>
              <thead>
                <tr>
                  <FirstHeaderColumn>Tipo de modelo</FirstHeaderColumn>
                  <HeaderColumn>Nome</HeaderColumn>
                  <HeaderColumn>Acurácia</HeaderColumn>
                  <HeaderColumn>Escore F1</HeaderColumn>
                  <HeaderColumn>Precisão</HeaderColumn>
                  <HeaderColumn><div style={{ display: 'flex', justifyContent: 'center' }}>Ações</div></HeaderColumn>
                </tr>
              </thead>

              <tbody>
                {
                  typesOfModels.map((item) => {
                    if(data[item] && data[item] !== []) {
                      return data[item].map((model, idx) => {
                        return this.renderItem(model, idx, item);
                      })
                    }
                  })
                }
              </tbody>
            </Table>
            : null}

          {this.renderMenuActions()}
          <AlertDialog onSubmit={this.deleteModel}></AlertDialog>
        </ConfigContainer >
      </PerfectScrollbar>
    )
  }
}

const mapStateToProps = ({ train_model }) => ({ train_model });

export default connect(mapStateToProps,
  {
    ...TrainModelActions, ...toastrActions,
    ...ModelCopyActions, ...DownloadActions,
    ...DialogActions
  })
  (TrainModel);