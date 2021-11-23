import React, { Component } from  'react';
import { CardContainer } from './styles';
import { Creators as DialogActions } from '../../store/ducks/dialog';
import { Creators as DataSourceActions } from '../../store/ducks/data_source';
import { connect } from 'react-redux';
import { default as CustomButton } from '../../styles/Button';
import { ConfigContainer } from '../../styles/ConfigContainer';
import { Header, fontFamily, primaryColor, StatusMsgContainer } from '../../styles/global';
import PerfectScrollbar from 'react-perfect-scrollbar';
import Card from '@material-ui/core/Card';
import CardActionArea from '@material-ui/core/CardActionArea';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';
import Chip from '@material-ui/core/Chip';
import DeleteIcon from 'react-feather/dist/icons/trash-2';
import FileIcon from 'react-feather/dist/icons/file';
import MoodleConfigDialog from '../MoodleConfigDialog';
import { FLOW, WIFI, SALES } from '../../constants';
import { Creators as ScreenActions } from '../../store/ducks/screen';
import { Creators as IndicatorActions } from '../../store/ducks/indicator';
import DataSourceDialog from '../DataSourceDialog';
import * as moment from 'moment';
import IconButton from '@material-ui/core/IconButton';
import { ProgressSpinner } from 'primereact/progressspinner';
import AlertDialog from '../AlertDialog';
import filesize from "filesize";
import api from '../../services/api';

const availableLms = { moodle: true };

class DataSource extends Component {

  state = {
    selectedItem: null,
    chipSelected: FLOW,
    loading: false,
    loadingMessage: 'Carregando os dados...'
  }

  componentWillMount() {
    this.props.getDataSource();
  }

  openDialogConfig = (item, event) => {
    if (!availableLms[item.name]) return;

    this.props.setDialog(item.name, {
      ...item,
      version: {
        label: item.version, value: item.version
      }
    })
  }

  renderCardCSV = (item, idx) => {

    if (item.typeOfData.toUpperCase() === this.state.chipSelected) {
      return (          
      <Card className='lms-card' key={idx}>
      <CardActionArea>
        <CardContent style={{ color: primaryColor }}>
          <Typography gutterBottom variant="h5" component="h2" style={{ fontFamily: fontFamily }}>
            {item.name}
          </Typography>
          <Typography variant="body2" color="textSecondary" component="p" style={{ color: primaryColor, fontFamily: fontFamily, fontSize: '10px' }}>
            <b>Importado em:</b> {moment(item.created_at).format('DD/MM/YYYY HH:mm')}
          </Typography>
          <Typography variant="body2" color="textSecondary" component="p" style={{ color: primaryColor, fontFamily: fontFamily, fontSize: '10px' }}>
            <b>Tamanho:</b> {filesize(item.size)}
          </Typography>
        </CardContent>
      </CardActionArea>
      <CardActions style={{ backgroundColor: primaryColor }}>
        <IconButton onClick={this.handleMsgDelete.bind(this, item)}>
          <DeleteIcon size={20} color={'#FFF'} />
        </IconButton>
      </CardActions>
    </Card>)
    } else {
      return null;
    }
  }

  handleMsgDelete = (item, event) => {
    this.setState({ selectedItem: item });

    this.props.setDialog('alert', {
      description: 'Você realmente deseja excluir esta fonte de dados?'
    });
  }

  handleDelete = () => {
    const { selectedItem } = this.state;

    if (!selectedItem || !selectedItem.id) return;

    this.props.deleteDataSource(selectedItem.id);
  }

  setChip = (value, event) => this.setState({ chipSelected: value });

  renderDatasetOptions = () => {
    const { chipSelected } = this.state;

    return (
      <div style={{ display: 'flex', paddingLeft: '2rem' }}>
        <div>
          <Chip
            avatar={<FileIcon size={16} color={chipSelected === FLOW ? '#FFF' : primaryColor} />}
            label="Dados de Fluxo"
            className={chipSelected === FLOW ? 'active-chip' : 'inactive-chip'}
            onClick={this.setChip.bind(this, FLOW)}
          />
        </div>
        <div style={{ paddingLeft: '.5vw' }}>
          <Chip
            avatar={<FileIcon size={16} color={chipSelected === WIFI ? '#FFF' : primaryColor} />}
            label="Dados de Wifi"
            className={chipSelected === WIFI ? 'active-chip' : 'inactive-chip'}
            onClick={this.setChip.bind(this, WIFI)}
          />
        </div>
        <div style={{ paddingLeft: '.5vw' }}>
          <Chip
            avatar={<FileIcon size={16} color={chipSelected === SALES ? '#FFF' : primaryColor} />}
            label="Dados de Vendas"
            className={chipSelected === SALES ? 'active-chip' : 'inactive-chip'}
            onClick={this.setChip.bind(this, SALES)}
          />
        </div>
      </div>
    )
  }

  addDataSource = () => this.props.setDialog('dataSource');

  startPreProcessing = () => {
    this.setState( {loading: true, loadingMessage: 'Pré processando os dados. Isto pode demorar, aguarde...'});
        api
        .post('prepr')
        .then(response => {
        })
        .catch((e) => {
        })
        .finally(() => {
          this.setState( {loading: false, loadingMessage: ''});
        }
        );
  }

  generateModel = () => {
    this.setState( {loading: true, loadingMessage: 'Gerando o modelo. Isto pode demorar, aguarde...'});
    api
    .post('train')
    .then(response => {
      console.log('resposta');
    })
    .catch((e) => {
      console.log(e);
    })
    .finally(() => {
      this.setState( {loading: false, loadingMessage: ''});
    }
    );
  }

  render() {
    const { chipSelected } = this.state;
    const { data_source } = this.props;
    const loading = !!data_source.loading || this.state.loading;
    const hasData = !!data_source.data.length;
    const loadingMessage = this.state.loadingMessage;
    // this.state.loadingMessage

    return (
      <PerfectScrollbar style={{ width: '100%', display: 'flex', flexDirection: 'row' }}>
        <ConfigContainer style={{ minHeight: '70%'}}>
          <Header>
            <h1>Fontes de Dados</h1>
          </Header>

          {loading? null : this.renderDatasetOptions()}
          {
            loading? null : <CardContainer>{data_source.data.map((item, idx) => this.renderCardCSV(item, idx))}</CardContainer>
          }

          {loading && (
            <StatusMsgContainer style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <h2 style={{ fontSize: 16, }}> { loadingMessage }</h2>
              <ProgressSpinner style={{ width: '50px', height: '50px' }} strokeWidth="4" fill="#EEEEEE" animationDuration=".5s" />
            </StatusMsgContainer>
          )}

          {!hasData && !loading && (
            <StatusMsgContainer>Nenhuma fonte de dados cadastrada</StatusMsgContainer>
          )}
        </ConfigContainer>

  
        <div style={{ minHeight: '70%', marginTop: '15vh', marginBottom: '20vh', backgroundColor: 'white',
                    display: 'flex', flexDirection: 'column', boxShadow: '4px 4px 4px 0px rgba(0, 0, 0, 0.1)',
                    borderRadius: '0 5px 5px 0'}}>
            <div style={{display: 'flex', justifyContent: 'center', marginTop: '32px'}}>
              <CustomButton
              disabled={loading}
              style={{padding: '1px', height: 'max-content', minHeight: '60px', margin: '5px', width: '80%'}}
              filled={false} onClick={this.addDataSource}>Adicionar fonte de dados</CustomButton>
            </div>
        <div style={{display: 'flex', justifyContent: 'center'}}>
              <CustomButton 
              disabled={loading}
              style={{padding: '1px', height: 'max-content', minHeight: '60px', margin: '5px', width: '80%'}}
              filled={false} onClick={this.startPreProcessing}>Iniciar pré-processamento</CustomButton>
            </div>
            <div style={{display: 'flex', justifyContent: 'center'}}>
              <CustomButton 
              disabled={loading}
              style={{padding: '1px', height: 'max-content', minHeight: '60px', margin: '5px', width: '80%'}}
              filled={false} onClick={this.generateModel}>Gerar Modelo</CustomButton>
            </div>
        </div>
        <MoodleConfigDialog />
        <DataSourceDialog typeOfData={chipSelected}/>
        <AlertDialog onSubmit={this.handleDelete}></AlertDialog>
      </PerfectScrollbar>
    );
  }
}

const mapStateToProps = ({ data_source }) => ({ data_source });

export default connect(
  mapStateToProps, {
  ...DialogActions,
  ...ScreenActions, ...IndicatorActions,
  ...DataSourceActions
}
)(DataSource);