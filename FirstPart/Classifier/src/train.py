import time
import copy
import torch


def evaluate_model(model, dataloader, device):
    model.eval()
    running_corrects = 0
    all_labels = []
    all_preds = []

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        with torch.no_grad():
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

        running_corrects += torch.sum(preds == labels.data)
        all_labels.extend([int(label) for label in labels.cpu().numpy()])
        all_preds.extend([int(pred) for pred in preds.cpu().numpy()])

    acc = running_corrects.double() / len(dataloader.dataset)
    return acc.item(), all_labels, all_preds


def update_best_model(stats, model, test_acc, test_labels, test_preds):
    stats['test_labels'] = test_labels
    stats['test_preds'] = test_preds
    best_acc = test_acc
    best_model_wts = copy.deepcopy(model.state_dict())
    return best_acc, best_model_wts
    



def train_model(model, dataloaders, criterion, optimizer, scheduler, device, num_epochs=30):
    since = time.time()
    
    stats = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': [],
        'test_acc': [],
        'test_labels': [],
        'test_preds': []
    }
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val', 'test']:                
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for batch_idx, (inputs, labels) in enumerate(dataloaders[phase]):
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    # Get model outputs and calculate loss
                    # In train mode we calculate the loss by summing the final output and the auxiliary output
                    # but in testing we only consider the final output.
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                    _, preds = torch.max(outputs, 1)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                    
                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)


            epoch_loss = running_loss / len(dataloaders[phase].dataset)
            epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))
                
            if phase == 'train':
                stats["train_acc"].append(epoch_acc.item())
                stats["train_loss"].append(epoch_loss)
                scheduler.step()  # Adjust the learning rate after each epoch
            elif phase == 'val':
                stats["val_acc"].append(epoch_acc.item())
                stats["val_loss"].append(epoch_loss) 
            elif phase == 'test':   
                # After each epoch, evaluate the model on the test set
                test_acc, test_labels, test_preds = evaluate_model(model, dataloaders['test'], device)
                print('Test Accuracy: {:4f}\n'.format(test_acc))
                stats['test_acc'].append(test_acc)
                if test_acc > best_acc:
                    best_acc, best_model_wts = update_best_model(stats, model, test_acc, test_labels, test_preds)
        
            

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    print('Best Test Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    
    return model, stats